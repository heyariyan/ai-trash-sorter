# Architecture

~~~text
U1 ultrasonic (<7 cm)
        ↓
Raspberry Pi state machine
 ├─ warm Pi camera → TFLite classifier
 ├─ IR-home + DRV8825 carousel
 ├─ GPIO18 MG995 gate
 ├─ U3 post-drop ultrasonic
 └─ Firebase Realtime Database / optional Storage
                                      ↓
                           Flutter operator app + Firebase Auth
~~~

The Raspberry Pi is autonomous. Firebase is best-effort and runs outside the physical sorting path. The Flutter app is an authenticated operator interface; it never owns GPIO or sends raw motor commands.

## State machine

~~~text
STARTING → HOMING → READY
READY → DETECTED → CAPTURING → CLASSIFYING → MOVING → DROPPING
      → MEASURING → WAITING_FOR_CLEAR → READY
~~~

An invalid U1 read does not transition state or actuate anything. A classification failure keeps the gate closed and records a diagnostic event. A movement failure closes the gate, sets carousel position to unknown, and enters ERROR; sorting is blocked until a safe homing request succeeds.

At startup the gate closes before bounded IR homing establishes logical stop 0. Four stops use 600 configured pulse steps/revolution by default: 150 steps/stop and 3 ms high + 3 ms low, or roughly 0.9 seconds per 90 degrees and 1.8 seconds for the maximum 180-degree move. The tie direction is forward_direction, making two-stop movement deterministic.

## Firebase layout

~~~text
devices/<device-id>/
  status/
  bins/<category>/
  events/<event-id>/
  feedback/<event-id>/
  commands/calibrate/
~~~

Events include class, confidence, bin, model version, inference/sorting timing, direction, steps, U3 distance, feedback state, and image lifecycle state. Calibration commands are polled on a background thread and only consumed when the machine is idle.

Temporary photos can be uploaded to the configured Firebase Storage bucket as devices/<device-id>/temporary/<event-id>.jpg; these are deleted on correct feedback or expiry. Incorrect feedback drives local retention and moves the cloud copy into feedback/<corrected-category>/.
