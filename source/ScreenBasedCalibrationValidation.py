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
                 timed_out,
                 coordinates,
                 gaze_data):
        self.__accuracy_left_eye = accuracy_left_eye
        self.__accuracy_right_eye = accuracy_right_eye
        self.__precision_left_eye = precision_left_eye
        self.__precision_right_eye = precision_right_eye
        self.__timed_out = timed_out
        self.__coordinates = coordinates
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
    def timed_out(self):
        return self.__timed_out

    @property
    def coordinates(self):
        return self.__coordinates

    @property
    def gaze_data(self):
        return self.__gaze_data


class CalibrationValidationResult(object):
    '''Represents a result of a calibration validation.
    '''

    def __init__(self,
                 points,
                 average_accuracy,
                 average_precision):
        self.__points = points
        self.__average_accuracy = average_accuracy
        self.__average_precision = average_precision

    @property
    def points(self):
        return self.__points

    @property
    def average_accuracy(self):
        return self.__average_accuracy

    @property
    def average_precision(self):
        return self.__average_precision


def _calculate_average_point(points):
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
    target_point3 = display_area_top_left + dx + dy
    return target_point3


def _calculate_eye_accuracy(gaze_origin_average, gaze_point_average, target_point3):
    '''Calculate angle difference between actual gaze point and target point.
    '''
    direction_gaze_point = vectormath.Vector3.from_points(gaze_origin_average, gaze_point_average).normalize()
    direction_target = vectormath.Vector3.from_points(gaze_origin_average, target_point3).normalize()
    accuracy = direction_target.angle(direction_gaze_point)
    return accuracy


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

        self.__data = []
        self.__data_map = []
        self.__current_point = None
        self.__is_collecting_data = False
        self.__validation_mode = False
        self.__timeout = False
        self.__timeout_thread = None
        self.__lock = threading.Lock()  # synchronization between timer and gaze data subscription callback
        self.__result = None

    def _calibration_timeout_handler(self):
        #print("_calibration_timeout_handler -- acquire lock...", flush=True)
        #self.__lock.acquire()
        #print("_calibration_timeout_handler -- lock acquired!", flush=True)
        if self.__is_collecting_data:
            self.__timeout = True
            self.__is_collecting_data = False
        #self.__lock.release()
        #print("_calibration_timeout_handler -- lock released!", flush=True)

    def _gaze_data_received(self, gaze_data):
        #print("_gaze_data_received -- acquire lock...", flush=True)
        #print("_gaze_data_received ({}) -- acquire lock...".format(threading.get_ident()), flush=True)
        #self.__lock.acquire()
        #print("_gaze_data_received -- lock acquired!", flush=True)
        if self.__is_collecting_data:
            if len(self.__data) < self.__sample_count:
                if gaze_data.left_eye.gaze_point.validity and gaze_data.right_eye.gaze_point.validity:
                    self.__data.append(gaze_data)
                    print("  got valid gaze data!", flush=True)
            else:
                # Data collecting stopped on sample count condition, timer might still be running
                self.__timeout_thread.cancel()

                # Data collecting done for this point
                self.__data_map.append((self.__current_point, self.__data))
                self.__data = []
                self.__is_collecting_data = False
                print("  got enough data!", flush=True)
        #self.__lock.release()
        #print("_gaze_data_received -- lock released!", flush=True)

    def enter_validation_mode(self):
        if self.__validation_mode or self.__is_collecting_data:
            raise RuntimeWarning("Validation mode already entered")

        self.__data_map = []
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
        self.__data = []
        self.__timeout = False
        self.__timeout_thread = threading.Timer(self.__timeout_ms / 1000.0, self._calibration_timeout_handler)
        self.__timeout_thread.start()
        self.__is_collecting_data = True

    def compute(self):
        if self.__is_collecting_data:
            raise RuntimeWarning("Still collecting data")

        points = []
        accuracy_left_eye_all = []
        accuracy_right_eye_all = []
        precision_left_eye_all = []
        precision_right_eye_all = []

        for target_point, samples in self.__data_map:
            if len(samples) < self.__sample_count:
                # Timeout before collecting enough valid samples, no calculations to be done
                points.append(CalibrationValidationPoint(target_point, -1, -1, -1, -1, True, samples))
                continue

            target_point3 = _calculate_normalized_point2_to_point3(self.__eye_tracker.get_display_area(), target_point)

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
            gaze_origin_left_average = _calculate_average_point(gaze_origin_left_all)
            gaze_origin_right_average = _calculate_average_point(gaze_origin_right_all)
            gaze_point_left_average = _calculate_average_point(gaze_point_left_all)
            gaze_point_right_average = _calculate_average_point(gaze_point_right_all)

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
                    vectormath.Vector3.from_points(gaze_origin_left, gaze_point_left_average).normalize())
                direction_gaze_point_right_all.append(
                    vectormath.Vector3.from_points(gaze_origin_right, gaze_point_right).normalize())
                direction_gaze_point_right_mean_all.append(
                    vectormath.Vector3.from_points(gaze_origin_right, gaze_point_right_average).normalize())

            # Accuracy calculations
            accuracy_left_eye = _calculate_eye_accuracy(
                gaze_origin_left_average, gaze_point_left_average, target_point3)
            accuracy_right_eye = _calculate_eye_accuracy(
                gaze_origin_right_average, gaze_point_right_average, target_point3)

            # Precision calculations
            precision_left_eye = _calculate_eye_precision(
                direction_gaze_point_left_all, direction_gaze_point_left_mean_all)
            precision_right_eye = _calculate_eye_precision(
                direction_gaze_point_right_all, direction_gaze_point_right_mean_all)

            # Add a calibration validation point
            points.append(CalibrationValidationPoint(
                target_point,
                accuracy_left_eye,
                accuracy_right_eye,
                precision_left_eye,
                precision_right_eye,
                False,  # no timeout
                samples))

            # Cache all calculations
            accuracy_left_eye_all.append(accuracy_left_eye)
            accuracy_right_eye_all.append(accuracy_right_eye)
            precision_left_eye_all.append(precision_left_eye)
            precision_right_eye_all.append(precision_right_eye)

        # Create a result
        num_points = len(accuracy_left_eye_all)
        if num_points > 0:
            accuracy_left_eye_average = sum(accuracy_left_eye_all) / num_points
            accuracy_right_eye_average = sum(accuracy_right_eye_all) / num_points
            accuracy_average = (accuracy_left_eye_average + accuracy_right_eye_average) / 2.0

            precision_left_eye_average = sum(precision_left_eye_all) / num_points
            precision_right_eye_average = sum(precision_right_eye_all) / num_points
            precision_average = (precision_left_eye_average + precision_right_eye_average) / 2.0
        else:
            accuracy_average = -1
            precision_average = -1

        self.__result = CalibrationValidationResult(points, accuracy_average, precision_average)
        return self.__result

    @property
    def collecting_data(self):
        '''Test if data collecting is in progess.
        '''
        return self.__is_collecting_data

    @property
    def result(self):
        '''Fetch the latest calibration result.
        '''
        return self.__result
