# Motion Gateway Module for FHEM

## An FHEMPY module to make use of motionblinds python library

### this module is intended to interface with a motionblind HUB

The motionblind HUB maintains the available binds it can control.
this module should be able to
+ if IP address and key of the hub specified, it connects to the HUB and request hte list of known devices
+ if the IP address of the hub is not specified, it search for a HUB and defines it accordingly


## MODE
+ sim, will use a predefinedd set of blinds as scan result
+  live scan of the network to detect the gateway/hub

  
