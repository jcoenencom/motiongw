import asyncio
from motionblinds import MotionGateway, MotionBlind
from motionblinds import MotionDiscovery

from .. import fhem, generic


DEVICE_TYPES_GATEWAY = ["02000001", "02000002"]  # Gateway
DEVICE_TYPE_BLIND = "10000000"  # Standard Blind
DEVICE_TYPE_TDBU = "10000001"  # Top Down Bottom Up
DEVICE_TYPE_DR = "10000002"  # Double Roller


class motiongw(generic.FhemModule):

    devtype = {"02000001":"Gateway", "02000002":"Gateway","10000000":"Standard Blind", "10000001":"Top/Down Bottom/Up", "10000002":"Double Roller"}


    def __init__(self, logger):
        super().__init__(logger)
        self.key = None
        self.IP = None
        self.mode = "sim"
        self.gateway = MotionGateway
        return

    # FHEM FUNCTION
    async def Define(self, hash, args, argsh):
        await super().Define(hash, args, argsh)

    # define the attributes

        self._attr_list = {
            "key": {"default": None},
            "IP": {"default": None},
        }

        await self.set_attr_config(self._attr_list)
        await self.set_icon("it_router")


    # check the defined attributes in the define command
        if len(args) > 5:
            self.IP = args[3]
            hash["IP"]= args[3]
            self.logger.info("Setting IP address")
            return "Usage: define NAME fhempy test IP"
            self.key = args[4]
            hash["key"] = args[4]

        self.logger.info(f"Define test address {self.IP}")


        
    
        self.logger.info(f"Define test key {self.IP}")

        set_config = {
            "mode": {
                "args": ["mode"],
                "argsh": ["mode"],
                "params": {"mode": {"default": "sim", "optional": False}},
                "options": "live,sim",
            },
            "scan": {
                # no parameters at the moment
            },
            "key": {
                "args": ["key"],
                "params": {"key": {"default": None, "optional": False}},                
            },
        }
        await self.set_set_config(set_config)

        await fhem.readingsSingleUpdate(hash, "mode", "sim", 1)

        await fhem.readingsBeginUpdate(hash)
        await fhem.readingsBulkUpdateIfChanged(self.hash, "state", "defined")
        await fhem.readingsEndUpdate(hash, 1)

    # depending on the IP and mode run the configuration

#        if self.IP == None:
#            self.logger.info(f"Undefined IP running a discover")
            #IP not defined run a discover
#        else:
#           self.logger.info(f"Getting Device info from the gateway")
            #IP is defined run a GetDevice
        

        # Attribute function format: set_attr_NAMEOFATTRIBUTE(self, hash)
        # self._attr_NAMEOFATTRIBUTE contains the new state
        async def set_attr_IP(self, hash):
            # attribute was set to self._attr_IP
            # you can use self._attr_interval already with the new variable
            pass

        # Set functions in format: set_NAMEOFSETFUNCTION(self, hash, params)

    async def __discover(self):
        if self.mode == "sim":
            mesg = {'192.168.1.100': {
                'msgType': 'GetDeviceListAck',
                'mac': 'abcdefghujkl',
                'deviceType': '02000002',
                'ProtocolVersion': '0.9',
                'token': '12345A678B9CDEFG',
                'data': [
                    {'mac': 'abcdefghujkl',     'deviceType': '02000002'},
                    {'mac': 'abcdefghujkl0001', 'deviceType': '10000000'},
                    {'mac': 'abcdefghujkl0002', 'deviceType': '10000000'}
                ]
            }}
            return mesg
        else:
            d = MotionDiscovery()
            mesg = d.discover()
            return d

    async def set_scan(self, hash, params):
        # Either scan for a gateway (no IP defined)
        # Or scan for devices
        if self.key == None:
            return "Define key attribute first"
        if self.IP == None:
            self.logger.info(f"calling discover routine")
            mesg = await self.__discover()
            # normally mesg holds the complete configuration of the discovered gateway/hub
            self.logger.info(mesg)
        else:
            self.logger.info(f"Getting Device info from the gateway")
            # IP is defined run a GetDevice
            # the discovery returns a disct for ecery gateway found
            # the ip address os the gateway is thus: list(mesg.keys())[0]
        self.IP = list(mesg.keys())[0]
        hash['IP']=self.IP
        await fhem.readingsBeginUpdate(hash)
        for key in mesg.keys():
            await fhem.readingsBulkUpdateIfChanged(self.hash, key, "GW IP defined")
            await fhem.readingsBulkUpdateIfChanged(self.hash, "state", "Discovery done")
            for k in mesg['192.168.1.100']['data']:
                await fhem.readingsBulkUpdateIfChanged(self.hash, k['mac'], self.devtype[k['deviceType']])
                if (k['deviceType'] == '10000000'):
                    # this is a standard blind, define the  fhempy device
                    await fhem.CommandDefine(
                        self.hash,
                        (
                            f"motionblinds_{k['mac']} fhempy motionblinds "
                            f"{self.IP} {self.key} {k['mac']} "
                            f"{k['deviceType']} "
                        ),
                    )
                elif (k['deviceType'] == '02000002'):
                # the gateway itself
                    self.gateway = MotionGateway(ip = self.IP, key = self.key)
                    hash['mac'] = k['mac']


            await fhem.readingsEndUpdate(hash, 1)

    async def set_key(self, hash, params):
        # attribute was set to self._key_interval
        # you can use self._attr_interval already with the new variable
        hash['key']=params['key']
        self.key = params['key']
        pass

    async def set_mode(self, hash, params):
        # user can specify mode as mode=eco or just eco as argument
        # params['mode'] contains the mode provided by user
        mode = params["mode"]
        await fhem.readingsSingleUpdate(hash, "mode", mode, 1)
        self.mode = mode

