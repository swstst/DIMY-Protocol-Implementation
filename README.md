# DIMY-Protocol-Implementation

## Changes From Official Protocol
- Broadcast is changed to every 3 seconds
- `t` seconds for `EphID` generation only `t ∈ {15,18,21,24,27,30}`
- `p` probability of dropping message only `p ∈ {30, 40, 50, 60, 70}`
- `k >= 3, n >= 5 and k < n`
- shares are shared every 3 seconds
- EphID generated every `t` seconds
- EphID does not overlap, so there is a possibility of no exchanges if timed perfectly
- using UDP and TCP not BLE, broadcasts are to everyone in local network
