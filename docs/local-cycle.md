# M8 offline local sorting cycle

Status: **Software and simulation complete; combined physical test pending.**

This milestone composes only the local path requested for the first integrated
test:

1. Start and home the stepper using GPIO23.
2. Run the quantized neural model on an existing image file.
3. Choose the material bin and move by the shortest calibrated path.
4. Open the GPIO18 MG995 gate at 90 degrees.
5. Close the gate at 0 degrees.
6. Report prediction, position plan, and measured stage/total timings.

The camera and ultrasonic sensors are deliberately excluded. Two existing Pi
image paths can be supplied to `motors`/`sorting.local_cycle_test`; no image is
captured during this test.

The physical command requires an explicit effective carousel
`--steps-per-revolution` value. The earlier 200-pulse observation produced only
about 120 degrees, so 200 must not be assumed for the installed mechanism.

The combined test is safety-sensitive because it energizes both the stepper and
servo in one sequence. Confirm the already-tested stepper/IR/servo conditions,
keep the mechanism clear, and authorize the combined cycle immediately before
running it. The command always homes first and shuts down all GPIO resources in
`finally`.
