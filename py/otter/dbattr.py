'''
Classes to standardize data that goes in or comes out of the Arango DB
'''
import numpy as np
import astropy.coordinates as coord
import astropy.units as u

class DBAttr(dict):
    '''
    Abstract db attribute
    '''

    # this will make it act more like a dictionary
    def __getitem__(self, items):
        return getattr(self, items)

    def tojson(self):        
        if isinstance(self.source, list):
            alias = ''
            for s in self.source:
                alias+=s.alias+','
            alias = alias[:-1]
        elif self.source is None:
            alias = ''
        else:
            alias = self.source.alias

        if len(alias) == 0:
            return {'value': self.value}
        else:
            return {'value': self.value, 'source':alias}
    
class Source(DBAttr):
    strname = 'sources'
    def __init__(self, sourceDict):
        '''
        Args:
            source [dict]: Contains at least keys with "name", "bibcode", "alias"
        '''

        self.name = sourceDict['name']
        self.bibcode = sourceDict['bibcode']
        self.alias = sourceDict['alias']
    
    def __eq__(self, src):
        return src.bibcode == self.bibcode

    def tojson(self):
        return {'name':self.name,
                'bibcode':self.bibcode,
                'alias':self.alias
                }

    @staticmethod
    def aliasToSource(alias, sourcemap):
        '''
        Converts the alias to a source object using the sourcemap
        '''
        alias = str(alias) # make sure it is a string
        if ',' in alias:
            return [sourcemap[a] for a in alias.split(',')]
        elif '-' in alias: # these are uuids
            return 'computed'
        else:
            return sourcemap[alias]
    
class RA(DBAttr):
    strname = 'ra'
    def __init__(self, ra, sourcemap=None):
        '''
        Args:
            ra [dict]: RA dict that can be in any of the following formats and must contain
                       the keys "ra" and "source"
                      - HH MM SS.SSSS
                      - HH:MM:SS.SSSS
        '''
        self.value = coord.Angle(ra['value'], unit=u.hourangle)
        self.valueString = self.value.to_string(unit=u.hourangle)
        
        if 'source' in ra and sourcemap is not None:
            src = Source.aliasToSource(ra['source'], sourcemap)
            self.source = src
        else:
            self.source = None

    def tojson(self):
        if isinstance(self.source, list):
            alias = ''
            for s in self.source:
                alias+=s.alias+','
            alias = alias[:-1]
        elif self.source is None:
            alias = ''
        else:
            alias = self.source.alias

        if len(alias) == 0:
            return {'value': self.valueString}
        else:
            return {'value': self.valueString, 'source':alias}
        
class Dec(DBAttr):
    strname = 'dec'
    def __init__(self, dec, sourcemap=None):
        '''
        Args:
            dec [dict]: Declination dict that can be in any of the following formats and must contain
                       the keys "dec" and "source"
                      - HH MM SS.SSSS
                      - HH:MM:SS.SSSS
        '''
        self.value = coord.Angle(dec['value'], unit=u.deg)
        self.valueString = self.value.to_string(unit=u.deg)
        
        if 'source' in dec and sourcemap is not None:
            src = Source.aliasToSource(dec['source'], sourcemap)
            self.source = src
        else:
            self.source = None

    def tojson(self):
        if isinstance(self.source, list):
            alias = ''
            for s in self.source:
                alias+=s.alias+','
            alias = alias[:-1]
        elif self.source is None:
            alias = ''
        else:
            alias = self.source.alias

        if len(alias) == 0:
            return {'value': self.valueString}
        else:
            return {'value': self.valueString, 'source':alias}
        
class Redshift(DBAttr):
    strname = 'z'
    def __init__(self, z, sourcemap=None):
        '''
        Args:
            z [list[dict]]: List of redshift dictionaries with keys 'z' and 'source'
        '''
        self.value = float(z['value'])
        if 'source' in z and len(z['source']) > 0 and sourcemap is not None:
            src = Source.aliasToSource(z['source'], sourcemap)
            self.source = src
        else:
            self.source = None

class Name(DBAttr):
    strname = 'name'
    def __init__(self, name, aliases=None):
        '''
        Args:
            name [str]: Primary key of the TDE 
            aliases [list[str]]: other names the TDE goes by
        '''
        self.name = name
        if aliases is not None:
            self.aliases = aliases
            
class DiscoveryDate(DBAttr):
    strname = 'discovery_date'
    def __init__(self, discoveryDate, sourcemap=None):
        '''
        Args:
            discoveryDate[list[dict]]: list of dictionaries of discover dates
        '''
        self.value = discoveryDate['value']
        if 'source' in discoveryDate and sourcemap is not None:
            src = Source.aliasToSource(discoveryDate['source'], sourcemap)
            self.source = src
        else:
            self.source = None
        
class Spectra(DBAttr):
    strname = 'spectra'
    def __init__(self, spectra, band, sourcemap=None):
        '''
        Args:
            spectra [list[dict]]: list of dictioanries of spectra
        '''
        self.spectra = spectra
        
class Photometry(DBAttr):
    strname = 'photometry'
    def __init__(self, photometry, band, sourcemap=None):
        '''
        Args:
            photometry [list[dict]]: list of photometry dictionaries
            band [str]: name of band this was measured at
        '''
        self.band = band
        self.reqKeys = {'time', 'luminosity', 'source'}
        self.time = []
        self.luminosity = []
        self.flux = []
        self.mag = []
        self.wavelength = []
        self.source = []
        self.upperlimit = []
        
        for d in photometry:
            if not self.reqKeys.issubset(d.keys()):
                raise Exception('time, luminosity, and source are required for every photometry point')

            # first add all the requried ones
            if isinstance(d['time'], list):
                self.time = np.mean(np.array(d['time']).astype(float))
            else:
                self.time.append(float(d['time']))
            
            self.source.append(Source.aliasToSource(d['source'], sourcemap))

            # some other optional ones
            if 'luminosity' in d:
                self.luminosity.append(float(d['luminosity']))
            else:
                self.luminosity.append(None)

            if 'flux' in d:
                self.flux.append(float(d['flux']))
            else:
                self.luminosity.append(None)

            if 'magnitude' in d:
                self.mag.append(float(d['magnitude']))
            else:
                self.mag.append(None)
                
            if 'wavelength' in d:
                self.wavelength.append(d['wavelength'])
            else:
                self.wavelength.append(None)

            if 'upperlimit' in d:
                self.upperlimit.append(True)
            else: # assume it is not an upper limit
                self.upperlimit.append(False)

        self.json = []
        for obs in photometry:
            d = {}
            for key in obs:
                if obs[key] is None: continue
                d[key] = obs[key]
            self.json.append(d)