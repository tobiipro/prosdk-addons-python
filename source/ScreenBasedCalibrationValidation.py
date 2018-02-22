import math
import threading

import tobii_research
from . import vectormath


class CalibrationValidationPoint(object):
    '''Represents a calibration validation point.
    '''

    def __init__(self,
                 accuracy_left_eye,
                 accuracy_right_eye,
                 precision_left_eye,
                 precision_right_eye,
                 rms_left_eye,
                 rms_right_eye,
                 timed_out,
                 screen_point,
                 gaze_data):
        self.__accuracy_left_eye = accuracy_left_eye
        self.__accuracy_right_eye = accuracy_right_eye
        self.__precision_left_eye = precision_left_eye
        self.__precision_right_eye = precision_right_eye
        self.__rms_left_eye = rms_left_eye
        self.__rms_right_eye = rms_right_eye
        self.__timed_out = timed_out
        self.__screen_point = screen_point
        self.__gaze_data = gaze_data

    @property
    def accuracy_left_eye(self):
        return self.__accuracy_left_eye

    @property
    def accuracy_right_eye(self):
        return self.__accuracy_right_eye

    @property
    def precision_left_eye(self):
        return self.__precision_left_eye

    @property
    def precision_right_eye(self):
        return self.__precision_right_eye

    @property
    def rms_left_eye(self):
        return self.__rms_left_eye

    @property
    def rms_right_eye(self):
        return self.__rms_right_eye

    @property
    def timed_out(self):
        return self.__timed_out

    @property
    def screen_point(self):
        return self.__screen_point

    @property
    def gaze_data(self):
        return self.__gaze_data


class CalibrationValidationResult(object):
    '''Represents a result of a calibration validation.
    '''

    def __init__(self,
                 points,
                 average_accuracy_left,
                 average_accuracy_right,
                 average_precision_left,
                 average_precision_right,
                 average_precision_rms_left,
                 average_precision_rms_right):
        self.__points = points
        self.__average_accuracy_left = average_accuracy_left
        self.__average_accuracy_right = average_accuracy_right
        self.__average_precision_left = average_precision_left
        self.__average_precision_right = average_precision_right
        self.__average_precision_rms_left = average_precision_rms_left
        self.__average_precision_rms_right = average_precision_rms_right

    @property
    def points(self):
        return self.__points

    @property
    def average_accuracy_left(self):
        return self.__average_accuracy_left

    @property
    def average_accuracy_right(self):
        return self.__average_accuracy_right

    @property
    def average_precision_left(self):
        return self.__average_precision_left

    @property
    def average_precision_right(self):
        return self.__average_precision_right

    @property
    def average_precision_rms_left(self):
        return self.__average_precision_rms_left

    @property
    def average_precision_rms_right(self):
        return self.__average_precision_rms_right


def _calculate_mean_point(points):
    '''Calculate an average point from a set of points
    '''
    average_point = vectormath.Point3()
    for point in points:
        average_point = average_point + point
    average_point = average_point * (1.0 / len(points))
    return average_point


def _calculate_normalized_point2_to_point3(display_area, target_point):
    display_area_top_right = vectormath.Point3.from_list(display_area.top_right)
    display_area_top_left = vectormath.Point3.from_list(display_area.top_left)
    display_area_bottom_left = vectormath.Point3.from_list(display_area.bottom_left)
    dx = (display_area_top_right - display_area_top_left) * target_point.x
    dy = (display_area_bottom_left - display_area_top_left) * target_point.y
    return display_area_top_left + dx + dy


def _calculate_eye_accuracy(gaze_origin_mean, gaze_point_mean, stimuli_point):
    '''Calculate angle difference between actual gaze point and target point.
    '''
    direction_gaze_point = vectormath.Vector3.from_points(gaze_origin_mean, gaze_point_mean).normalize()
    direction_target = vectormath.Vector3.from_points(gaze_origin_mean, stimuli_point).normalize()
    return direction_target.angle(direction_gaze_point)


def _calculate_eye_precision(direction_gaze_point_list, direction_gaze_point_mean_list):
    '''Calculate standard deviation of gaze point angles.
    '''
    angles = []
    for dir_gaze_point, dir_gaze_point_mean in zip(direction_gaze_point_list, direction_gaze_point_mean_list):
        angles.append(dir_gaze_point.angle(dir_gaze_point_mean))
    variance = sum([x**2 for x in angles]) / len(angles)
    if variance > 0.0:
        standard_deviation = math.sqrt(variance)
    else:
        standard_deviation = 0.0
    return standard_deviation


def _calculate_eye_precision_rms(direction_gaze_point_list):
    '''Calculate root mean square (RMS) of gaze point angles.
    '''
    consecutive_angle_diffs = []
    last_gaze_point_vector = direction_gaze_point_list[0]
    for gaze_point_vector in direction_gaze_point_list[1:]:
        consecutive_angle_diffs.append(gaze_point_vector.angle(last_gaze_point_vector))
    variance = sum([x**2 for x in consecutive_angle_diffs]) / len(consecutive_angle_diffs)
    if variance > 0.0:
        rms = math.sqrt(variance)
    else:
        rms = 0.0
    return rms


class ScreenBasedCalibrationValidation(object):
    '''Provides methods and properties for screen based calibration validation.
    '''
    SAMPLE_COUNT_MIN = 10
    SAMPLE_COUNT_MAX = 3000
    TIMEOUT_MIN = 100  # ms
    TIMEOUT_MAX = 3000  # ms

    def __init__(self,
                 eye_tracker,
                 sample_count=30,
                 timeout_ms=1000):
        if eye_tracker is None:
            raise ValueError("Eye tracker is none")
        self.__eye_tracker = eye_tracker

        if sample_count < self.SAMPLE_COUNT_MIN or sample_count > self.SAMPLE_COUNT_MAX:
            raise ValueError("Samples must be between 10 and 3000")
        self.__sample_count = sample_count

        if timeout_ms < self.TIMEOUT_MIN or timeout_ms > self.TIMEOUT_MAX:
            raise ValueError("Timeout must be between 100 and 3000")
        self.__timeout_ms = timeout_ms

        self.__current_point = None
        self.__current_gaze_data = []
        self.__collected_points = []

        self.__is_collecting_data = False
        self.__validation_mode = False

        self.__timeout = False
        self.__timeout_thread = None
        self.__lock = threading.Lock()  # synchronization between timer and gaze data subscription callback
        self.__result = None

    def _calibration_timeout_handler(self):
        # print("_calibration_timeout_handler -- acquire lock...", flush=True)
        # self.__lock.acquire()
        # print("_calibration_timeout_handler -- lock acquired!", flush=True)
        if self.__is_collecting_data:
            self.__timeout = True
            self.__is_collecting_data = False
        # self.__lock.release()
        # print("_calibration_timeout_handler -- lock released!", flush=True)

    def _gaze_data_received(self, gaze_data):
        # print("_gaze_data_received -- acquire lock...", flush=True)
        # print("_gaze_data_received ({}) -- acquire lock...".format(threading.get_ident()), flush=True)
        # self.__lock.acquire()
        # print("_gaze_data_received -- lock acquired!", flush=True)
        if self.__is_collecting_data:
            if len(self.__current_gaze_data) < self.__sample_count:
                if gaze_data.left_eye.gaze_point.validity and gaze_data.right_eye.gaze_point.validity:
                    self.__current_gaze_data.append(gaze_data)
                    # print("  got valid gaze data!", flush=True)
            else:
                # Data collecting stopped on sample count condition, timer might still be running
                self.__timeout_thread.cancel()

                # Data collecting done for this point
                self.__collected_points.append((self.__current_point, self.__current_gaze_data))
                self.__current_gaze_data = []
                self.__is_collecting_data = False
                # print("  got enough data!", flush=True)
        # self.__lock.release()
        # print("_gaze_data_received -- lock released!", flush=True)

    def enter_validation_mode(self):
        if self.__validation_mode or self.__is_collecting_data:
            raise RuntimeWarning("Validation mode already entered")

        self.__collected_points = []
        self.__result = None
        self.__eye_tracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA, self._gaze_data_received)
        self.__validation_mode = True

    def leave_validation_mode(self):
        if not self.__validation_mode:
            raise RuntimeWarning("Not in validation mode")
        if self.__is_collecting_data:
            raise RuntimeWarning("Cannot leave validation mode while collecting data")

        self.__current_point = None
        self.__eye_tracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA, self._gaze_data_received)
        self.__validation_mode = False

    def start_collecting_data(self, screen_point):
        if not self.__validation_mode:
            raise RuntimeWarning("Not in validation mode")
        if self.__is_collecting_data:
            raise RuntimeWarning("Already collecting data")

        self.__current_point = screen_point
        self.__current_gaze_data = []
        self.__timeout = False
        self.__timeout_thread = threading.Timer(self.__timeout_ms / 1000.0, self._calibration_timeout_handler)
        self.__timeout_thread.start()
        self.__is_collecting_data = True

    def clear(self):
        if self.__is_collecting_data:
            raise RuntimeWarning("Attempted to discard data while collecting data")

        self.__current_point = None
        self.__current_gaze_data = []
        self.__collected_points = []
        self.__result = None

    def discard_data(self, screen_point):
        if not self.__validation_mode:
            raise RuntimeWarning("Not in validation mode, no points to discard")
        if self.__is_collecting_data:
            raise RuntimeWarning("Attempted to discard data while collecting data")
        if self.__collected_points is None or len(self.__collected_points) == 0:
            raise RuntimeWarning("Attempt to discard non-collected point")

        # self.__lock.acquire()
        pre_discarding_length = len(self.__collected_points)
        print("Collected points before discard:")
        for x in self.__collected_points:
            print("  {}: {}".format(x[0], x[1]))
        self.__collected_points = [x for x in self.__collected_points if x[0] != screen_point]
        post_discarding_length = len(self.__collected_points)
        # self.__lock.release()

        if pre_discarding_length == post_discarding_length:
            raise RuntimeWarning("Attempt to discard non-collected point")

    def compute(self):
        if self.__is_collecting_data:
            raise RuntimeWarning("Still collecting data")

        points = []
        accuracy_left_eye_all = []
        accuracy_right_eye_all = []
        precision_left_eye_all = []
        precision_right_eye_all = []
        precision_rms_left_eye_all = []
        precision_rms_right_eye_all = []

        for screen_point, samples in self.__collected_points:
            if len(samples) < self.__sample_count:
                # Timeout before collecting enough valid samples, no calculations to be done
                points.append(CalibrationValidationPoint(screen_point, -1, -1, -1, -1, -1, -1, True, samples))
                continue

            stimuli_point = _calculate_normalized_point2_to_point3(self.__eye_tracker.get_display_area(), screen_point)

            # Prepare data from samples
            gaze_origin_left_all = []
            gaze_origin_right_all = []
            gaze_point_left_all = []
            gaze_point_right_all = []
            direction_gaze_point_left_all = []
            direction_gaze_point_left_mean_all = []
            direction_gaze_point_right_all = []
            direction_gaze_point_right_mean_all = []

            for sample in samples:
                gaze_origin_left_all.append(
                    vectormath.Point3.from_list(sample.left_eye.gaze_origin.position_in_user_coordinates))
                gaze_origin_right_all.append(
                    vectormath.Point3.from_list(sample.right_eye.gaze_origin.position_in_user_coordinates))
                gaze_point_left_all.append(
                    vectormath.Point3.from_list(sample.left_eye.gaze_point.position_in_user_coordinates))
                gaze_point_right_all.append(
                    vectormath.Point3.from_list(sample.right_eye.gaze_point.position_in_user_coordinates))
            gaze_origin_left_mean = _calculate_mean_point(gaze_origin_left_all)
            gaze_origin_right_mean = _calculate_mean_point(gaze_origin_right_all)
            gaze_point_left_mean = _calculate_mean_point(gaze_point_left_all)
            gaze_point_right_mean = _calculate_mean_point(gaze_point_right_all)

            for sample in samples:
                gaze_origin_left = vectormath.Point3.from_list(
                    sample.left_eye.gaze_origin.position_in_user_coordinates)
                gaze_origin_right = vectormath.Point3.from_list(
                    sample.right_eye.gaze_origin.position_in_user_coordinates)
                gaze_point_left = vectormath.Point3.from_list(
                    sample.left_eye.gaze_point.position_in_user_coordinates)
                gaze_point_right = vectormath.Point3.from_list(
                    sample.right_eye.gaze_point.position_in_user_coordinates)
                direction_gaze_point_left_all.append(
                    vectormath.Vector3.from_points(gaze_origin_left, gaze_point_left).normalize())
                direction_gaze_point_left_mean_all.append(
                    vectormath.Vector3.from_points(gaze_origin_left, gaze_point_left_mean).normalize())
                direction_gaze_point_right_all.append(
                    vectormath.Vector3.from_points(gaze_origin_right, gaze_point_right).normalize())
                direction_gaze_point_right_mean_all.append(
                    vectormath.Vector3.from_points(gaze_origin_right, gaze_point_right_mean).normalize())

            # Accuracy calculations
            accuracy_left_eye = _calculate_eye_accuracy(gaze_origin_left_mean, gaze_point_left_mean, stimuli_point)
            accuracy_right_eye = _calculate_eye_accuracy(gaze_origin_right_mean, gaze_point_right_mean, stimuli_point)

            # Precision calculations
            precision_left_eye = _calculate_eye_precision(
                direction_gaze_point_left_all, direction_gaze_point_left_mean_all)
            precision_right_eye = _calculate_eye_precision(
                direction_gaze_point_right_all, direction_gaze_point_right_mean_all)

            # RMS precision calculations
            precision_rms_left_eye = _calculate_eye_precision_rms(direction_gaze_point_left_all)
            precision_rms_right_eye = _calculate_eye_precision_rms(direction_gaze_point_right_all)

            # Add a calibration validation point
            points.append(CalibrationValidationPoint(
                screen_point,
                accuracy_left_eye,
                accuracy_right_eye,
                precision_left_eye,
                precision_right_eye,
                precision_rms_left_eye,
                precision_rms_right_eye,
                False,  # no timeout
                samples))

            # Cache all calculations
            accuracy_left_eye_all.append(accuracy_left_eye)
            accuracy_right_eye_all.append(accuracy_right_eye)
            precision_left_eye_all.append(precision_left_eye)
            precision_right_eye_all.append(precision_right_eye)
            precision_rms_left_eye_all.append(precision_rms_left_eye)
            precision_rms_right_eye_all.append(precision_rms_right_eye)

        # Create a result
        num_points = len(accuracy_left_eye_all)
        if num_points > 0:
            accuracy_left_eye_average = sum(accuracy_left_eye_all) / num_points
            accuracy_right_eye_average = sum(accuracy_right_eye_all) / num_points
            precision_left_eye_average = sum(precision_left_eye_all) / num_points
            precision_right_eye_average = sum(precision_right_eye_all) / num_points
            precision_rms_left_eye_average = sum(precision_rms_left_eye_all) / num_points
            precision_rms_right_eye_average = sum(precision_rms_right_eye_all) / num_points
        else:
            accuracy_left_eye_average = -1
            accuracy_right_eye_average = -1
            precision_left_eye_average = -1
            precision_right_eye_average = -1
            precision_rms_left_eye_average = -1
            precision_rms_right_eye_average = -1

        self.__result = CalibrationValidationResult(points,
                                                    accuracy_left_eye_average,
                                                    accuracy_right_eye_average,
                                                    precision_left_eye_average,
                                                    precision_right_eye_average,
                                                    precision_rms_left_eye_average,
                                                    precision_rms_right_eye_average)
        return self.__result

    @property
    def collecting_data(self):
        '''Test if data collecting is in progess.
        '''
        return self.__is_collecting_data

    @property
    def validation_mode(self):
        return self.__validation_mode

    @property
    def result(self):
        '''Fetch the latest calibration result.
        '''
        return self.__result
