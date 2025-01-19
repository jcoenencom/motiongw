import asyncio
from motionblinds import MotionGateway, MotionBlind
from motionblinds import MotionDiscovery

from .. import fhem, generic


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

        await self.set_icon("it_router")
        await fhem.CommandAttr(self.hash, self.hash["NAME"] + " verbose 5")

    # check the defined attributes in the define command
        if len(args) >= 4:
            self.IP = args[3]
            hash["IP"]= args[3]
            self.logger.info("Setting IP address")
            self.key = args[4]
            hash["key"] = args[4]

        self.logger.info(f"Define test address {self.IP}")


        
    
        self.logger.info(f"Define test key {self.key}")

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
        
    async def __getDevList(self):
        # create the MotionGateway instance
        # sim mode, populated devices in gw instance
        # live request the devlist to the gateway
        self.gw = MotionGateway(ip=self.IP, key=self.key)
        self.logger.debug(f"Internal getDevList: instanciate gw IP={self.IP} KEY={self.key}")

        if self.mode == "sim":
            obj1 = MotionBlind(gateway=self.gw, mac='123456789', device_type='RollerBlind')
            obj2 = MotionBlind(gateway=self.gw, mac='987654321', device_type='RollerBlind')
            # assign the object to the gateway device list, the key is the Mac address
            self.gw.device_list[obj1.mac]=obj1
            self.gw.device_list[obj2.mac]=obj2
            self.logger.debug(f"Internal getDevList: sim defined 2 blinds in gw")
            return
        else:
            self.logger.debug(f"Internal getDevList: live interogate gw")
            self.gw.GetDeviceList()
            self.gw.Update()
            return 
        
    async def set_scan(self, hash, params):
        # Perform a discovery calling internal __discover routine that discriminate between sim and live mode
        # IP beig the first parameter of the define in fhem, if not set, key is also not set
        if self.IP == None:
            # no IP run a discovery
            self.logger.debug(f"calling discover routine")
            mesg = await self.__discover()
            # normally mesg holds the complete configuration of the discovered gateway/hub
            self.logger.debug(mesg)
            # get the IP from the discover message and set it on the gw obj
            self.IP = list(mesg.keys())[0]
            hash['IP']=self.IP
            await fhem.readingsBeginUpdate(hash)
            for key in mesg.keys():
                await fhem.readingsBulkUpdateIfChanged(self.hash, "state", "Discovery done")
                # define each device known to the HUB as motionblinds instance of fhem
                for k in mesg[self.IP]['data']:
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
        elif self.key != None :
            # IP and key are set we can do a GetDeviceList
            self.logger.info(f"Getting Device info from the gateway {self.IP}")
            mesg = await self.__getDevList()
            for blind in self.gw.device_list.values():
                self.logger.debug(f"gw scan: device_list.value loop: issuing fhem define motionblinds_{blind.mac} fhempy motionblinds {self.IP} {self.key} {blind.mac} {blind.device_type}")
                await fhem.CommandDefine(
                    self.hash,
                    (
                        f"motionblinds_{blind.mac} fhempy motionblind "
                        f"{self.IP} {self.key} {blind.mac} "
                        f"{blind.device_type} "
                    ),
                )
        else:
            return "IP is defined but no access key required by gateway communication, please define one"

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
