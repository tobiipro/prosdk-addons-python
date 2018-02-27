# prosdk-addons-python

## What is it
Addons for the Tobii Pro SDK.

![alt text](https://www.tobiipro.com/imagevault/publishedmedia/6rkt3jb83qlottsfh1ts/Tobii-Pro-SDK-with-VR-3_1-banner.jpg)


The Tobii Pro SDK is available at: https://www.tobiipro.com/product-listing/tobii-pro-sdk/
Documentation to the API: http://developer.tobiipro.com/matlab.html


### Calibration Validation
* To use this feature it is necessary to install the tobii-research package from PyPI, see [getting started](http://developer.tobiipro.com/python/python-getting-started.html).
* Next just download or clone this folder to your own python project directory.


Do not hesitate to contribute to this project and create issues if you find something that might be wrong or could be improved.

#### Example
Before starting a calibration validation, it is needed some setup with the desired tracker.

```
import time
import tobii_research as tr
from tobii_research_addons import ScreenBasedCalibrationValidation, Point2

eyetracker_address = 'Replace the address of the desired tracker'
eyetracker = tr.EyeTracker(eyetracker_address)
```

Now it is possible to create a calibration validation object with the eye tracker object previously created.
More infotmation about this class and its methods can be found in the [ScreenBasedCalibrationValidation](./source/ScreenBasedCalibrationValidation.py) definition.

```
sample_count = 30
timeout_ms = 1000

calib = ScreenBasedCalibrationValidation(eyetracker, sample_count, timeout_ms)
```

The next step is to enter validation mode. Note that this action will lead to the tracker to start collecting gaze data.

```
calib.enter_validation_mode()
```

List the points that are to be used during the validation.

```
points_to_collect = [Point2(0.1, 0.1), Point2(0.1, 0.9), Point2(0.5, 0.5), Point2(0.9, 0.1), Point2(0.9, 0.9)]
```

When collecting data a point should be presented on the screen in the appropriate position.

```
for point in points_to_collect:
    # Visualize point on screen
    # ...
    calib.start_collecting_data(point)
    while calib.is_collecting_data:
        time.sleep(0.5)
```

Next just call the compute method to obtain the calibration validation object.

```
calibration_result = calib.compute()
```

Now the calibration result should be available for inspection.

More information about the calibration validation result can be found in the [CalibrationValidationResult](./source/ScreenBasedCalibrationValidation.py) class.

If the result is satisfactory then the only thing left to do is to leave validation mode.
This action will clear all the data collected in the current validation session and will stop the gaze data collection
from the tracker.

```
calib.leave_validation_mode()
```
