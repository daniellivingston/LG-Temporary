from pexpect import spawn
from subprocess import call, PIPE
import os
import glob
import re

class PyLaGriT(spawn):
    ''' Python lagrit class'''
    def __init__(self, lagrit_exe=None, verbose=True, batch=False, batchfile='pylagrit.lgi', gmv_exe=None, paraview_exe=None, *args, **kwargs):
        self.verbose = verbose
        self.mo = {}
        self.surface = {}
        self.region = {}
        self.batch = batch
        self._check_rc()
        if lagrit_exe is not None: self.lagrit_exe = lagrit_exe
        if gmv_exe is not None: self.gmv_exe = gmv_exe
        if paraview_exe is not None: self.paraview_exe = paraview_exe        
        if self.batch:
            try: self.fh = open(batchfile, 'w')
            except IOError as e: 
                print "Unable to open "+batchfile+": {1}".format(e.strerror)
                print "Batch mode disabled"
                self.batch = False
            else:
                self.batchfile = batchfile
                self.fh.write('# PyLaGriT generated LaGriT script\n')
        else:
            super(PyLaGriT, self).__init__(self.lagrit_exe, timeout=300, *args, **kwargs) 
            self.expect()
            if verbose: print self.before
    def run_batch(self):
        self.fh.write('finish\n')
        self.fh.close()
        if self.verbose:
            call(self.lagrit_exe+' < '+self.batchfile, shell=True)
        else:
            fout=open('pylagrit.stdout','w')
            call(self.lagrit_exe+' < '+self.batchfile, shell=True, stdout=fout)
            fout.close()
    def expect(self, expectstr='Enter a command'):
        if self.batch:
            print "expect disabled during batch mode"
        else:
            super(PyLaGriT, self).expect(expectstr) 
    def sendline(self, cmd, verbose=True, expectstr='Enter a command'):
        if self.batch:
            self.fh.write(cmd+'\n')
        else:
            super(PyLaGriT, self).sendline(cmd) 
            self.expect(expectstr=expectstr)
            if verbose and self.verbose: print self.before
    def interact(self, escape_character='^'):
        if self.batch:
            print "Interactive mode unavailable during batch mode"
        else:
            print "\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
            print "Entering interactive mode"
            print "To return to python terminal, type a '"+escape_character+"' character"
            print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n"
            print self.after
            super(PyLaGriT, self).interact(escape_character=escape_character) 
    def cmo_status(self, cmo=None, brief=False):
        cmd = 'cmo/status'
        if cmo: cmd += '/'+cmo 
        if brief: cmd += '/brief'
        self.sendline(cmd)
    def read(self,filename,filetype=None,name=None,binary=False):
        # If filetype is lagrit, name is irrelevant
        if filetype is not None:
            cmd = '/'.join(['read',filetype])
        else:
            cmd = 'read'
        if filetype != 'lagrit':
            if name is None:
                name = make_name('mo',self.mo.keys())
            cmd = '/'.join([cmd,filename,name])
        else:
            cmd = '/'.join([cmd,filename,'dum'])
        if binary: cmd = '/'.join([cmd,'binary'])
        self.sendline(cmd)
        # If format lagrit, cmo read in will not be set to name
        if format == 'lagrit' and not self.batch:
            self.sendline('cmo/status/brief', verbose=False)
            for line in self.before.split('\r\n'):
                if 'current-mesh-object' in line:
                    tmp_name = line.split(':')[1].strip()
                    if name is None: name = tmp_name
                    elif name != tmp_name: 
                        self.sendline('cmo/copy/'+name+'/'+tmp_name)
                        self.sendline('cmo/release/'+tmp_name)
        self.mo[name] = MO(name,self)
        return self.mo[name]
    def addmesh(self, mo1, mo2, style='add', name=None, *args):
        if isinstance(mo1,MO): mo1name = mo1.name
        elif isinstance(mo1,str): mo1name = mo1
        else:
            print "ERROR: MO object or name of mesh object as a string expected for mo1"
            return
        if isinstance(mo2,MO): mo2name = mo2.name
        elif isinstance(mo2,str): mo2name = mo2
        else:
            print "ERROR: MO object or name of mesh object as a string expected for mo2"
            return
        if name is None:
            name = make_name('mo',self.mo.keys())
        cmd = '/'.join(['addmesh',style,name,mo1name,mo2name])
        for a in args: 
            if isinstance(a, str):
                cmd = '/'.join([cmd,a])
            elif isinstance(a,list):
                cmd = '/'.join([cmd,' '.join([str(v) for v in a])])
        self.sendline(cmd)
        self.mo[name] = MO(name,self)
        return self.mo[name]
    def addmesh_add(self, mo1, mo2, name=None, refine_factor=None, refine_style='edge'):
        if refine_factor is None: refine_factor = ' '
        return self.addmesh( mo1, mo2, 'add', name, refine_factor, refine_style )
    def addmesh_amr(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='amr', name=name )
    def addmesh_append(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='append', name=name )
    def addmesh_delete(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='delete', name=name )
    def addmesh_glue(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='glue', name=name )
    def addmesh_intersect(self, pset, mo1, mo2, name=None):
        if isinstance(pset,PSet): psetname = pset.name
        elif isinstance(pset,str): psetname = pset
        else:
            print "ERROR: PSet object or name of PSet object as a string expected for pset"
            return
        if isinstance(mo1,MO): mo1name = mo1.name
        elif isinstance(mo1,str): mo1name = mo1
        else:
            print "ERROR: MO object or name of mesh object as a string expected for mo1"
            return
        if isinstance(mo2,MO): mo2name = mo2.name
        elif isinstance(mo2,str): mo2name = mo2
        else:
            print "ERROR: MO object or name of mesh object as a string expected for mo2"
            return
        if name is None:
            name = make_name('mo',self.mo.keys())
        cmd = '/'.join(['addmesh','intersect',name,psetname,mo1name,mo2name])        
        self.sendline(cmd)
        self.pset[name] = PSet(name,self)
        return self.pset[name]
    def addmesh_merge(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='merge', name=name )
    def addmesh_pyramid(self, mo1, mo2, name=None):
        return self.addmesh( mo1, mo2, style='pyramid', name=name )
    def addmesh_excavate(self, mo1, mo2, name=None, bfs=False, connect=False):
        if bfs: bfsstr = 'bfs'
        else: bfsstr = ' '
        if connect: connectstr = 'connect'
        else: connectstr = ' '
        return self.addmesh( mo1, mo2, 'excavate', name, bfsstr, connectstr )
    def surface_box(self,mins,maxs,name=None,ibtype='reflect'):
        if name is None:
            name = make_name('s',self.surface.keys())
        mins = [str(v) for v in mins]
        maxs = [str(v) for v in maxs]
        cmd = '/'.join(['surface',name,ibtype,'box',','.join(mins),','.join(maxs)])
        self.sendline(cmd)
        self.surface[name] = Surface(name,self)
        return self.surface[name]
    def surface_cylinder(self,coord1,coord2,radius,name=None,ibtype='reflect'):
        if name is None:
            name = make_name('s',self.surface.keys())
        coord1 = [str(v) for v in coord1]
        coord2 = [str(v) for v in coord2]
        cmd = '/'.join(['surface',name,ibtype,'cylinder',','.join(coord1),','.join(coord2),str(radius)])
        self.sendline(cmd)
        self.surface[name] = Surface(name,self)
        return self.surface[name]
    def region_bool(self,bool,name=None): 
        if name is None:
            name = make_name('r',self.region.keys())
        cmd = '/'.join(['region',name,bool])
        self.sendline(cmd)
        self.region[name] = Region(name,self)
        return self.region[name]
    def _check_rc(self):
        # check if pyfehmrc file exists
        rc_wd1 = os.sep.join(os.getcwd())+os.sep+'.pylagritrc'
        rc_wd2 = os.sep.join(os.getcwd())+os.sep+'pylagritrc'
        rc_home1 = os.path.expanduser('~')+os.sep+'.pylagritrc'
        rc_home2 = os.path.expanduser('~')+os.sep+'pylagritrc'
        if os.path.isfile(rc_wd1): fp = open(rc_lib1)
        elif os.path.isfile(rc_wd2): fp = open(rc_lib2)
        elif os.path.isfile(rc_home1): fp = open(rc_home1)
        elif os.path.isfile(rc_home2): fp = open(rc_home2)
        else: return
        lns = fp.readlines()
        for ln in lns:
            ln = ln.split('#')[0]       # strip off the comment
            if ln.startswith('#'): continue
            elif ln.strip() == '': continue
            elif ':' in ln:
                v = ln.split(':')
                if v[0].strip() == 'lagrit_exe':
                    self.lagrit_exe = v[1].strip()
                elif v[0].strip() == 'gmv_exe':
                    self.gmv_exe = v[1].strip()
                elif v[0].strip() == 'paraview_exe':
                    self.paraview_exe = v[1].strip()
                else:
                    print 'WARNING: unrecognized .pylagritrc line \''+ln.strip()+'\''
            else:
                print 'WARNING: unrecognized .pylagritrc line \''+ln.strip()+'\''
    def extract_surfmesh(self,name=None,cmo_in=None,stride=[1,0,0],reorder=False):
        if name is None:
            name = make_name('mo',self.mo.keys())
        if cmo_in is not None:
            if not isinstance( cmo_in, MO):
                print "ERROR: MO object or name of mesh object as a string expected for cmo_in"
                return
        if reorder:
            cmo_in.sendline('createpts/median')
            self.sendline('/'.join(['sort',cmo_in.name,'index/ascending/ikey/itetclr zmed ymed zmed']))
            self.sendline('/'.join(['reorder',cmo_in.name,'ikey']))
            self.sendline('/'.join(['cmo/DELATT',cmo_in.name,'xmed']))
            self.sendline('/'.join(['cmo/DELATT',cmo_in.name,'ymed']))
            self.sendline('/'.join(['cmo/DELATT',cmo_in.name,'zmed']))
            self.sendline('/'.join(['cmo/DELATT',cmo_in.name,'ikey']))
        stride = [str(v) for v in stride]
        self.sendline( '/'.join(['extract/surfmesh',','.join(stride),name,cmo_in.name]))
        self.mo[name] = MO(name,self)
        return self.mo[name] 
              
    def read_script(self, fname):
        '''
        Read a LaGriT Script
        
        Given a script name, executes the script in LaGriT. 
        
        :param fname: The name or path to the lagrit script.
        :type fname: str
        '''     
           
        f = open(fname)
        commands = f.readlines()   
        for c in commands:
            #Remove newlines and spaces
            c = ''.join(c.split())
            if len(c) != 0 and 'finish' not in c:
                self.sendline(c)
                            
    def convert(self, pattern, new_ft):
        '''
        Convert File(s)
        
        For each file of the pattern, creates a new file in the new_ft format. 
        The new files will be inside the directory that the LaGriT object was
        instantiated. The name of each file will be the same as the original 
        file with the extension changed to new_ft.
        
        Supports conversion from avs, and gmv files.
        Supports conversion to avs, exo, and gmv files.
         
        :param pattern: Path, name or unix style file pattern of files to be 
                        converted.
        :type  pattern: str
        
        :param new_ft: New format to convert files.
        :type  new_ft: str
        '''
        
        #Make sure I support the new filetype.
        if new_ft not in ['avs', 'gmv', 'exo']:
            raise ValueError('Conversion to %s not supported.'%new_ft)
        
        #Make sure there are file patterns of this type.
        fnames = glob.glob(pattern)
        if len(fnames) ==  0:
            raise OSError('No files found matching that name or pattern.')
        
        for rpath in fnames:
            #Set everything up for lagrit.
            path = os.path.abspath(rpath)
            fname = path[path.rfind('/')+1:path.rfind('.')]
            old_ft = path[path.rfind('.')+1:]
            
            #Check that I support the old filetype.
            if old_ft not in ['avs', 'gmv']:
                raise ValueError('Conversion from %s not supported.'%old_ft)
  
            try:
                os.symlink(path, 'old_format')   
            except OSError as err:
                raise err('Unable to create a symbolic link.') 
                  
            #Run the commands in lagrit.
            self.sendline('read/%s/old_format/temp_cmo'%old_ft)   
            self.sendline('dump/%s/%s.%s/temp_cmo'%(new_ft, fname, new_ft))

            #Clean up created data.
            self.sendline('cmo/release/temp_cmo')
            os.unlink('old_format')
            
    def merge(self, *mesh_objs):
        '''
        Merge Mesh Objects
        
        Merges two or more mesh objects together and returns the combined mesh
        object.
        
        :param mesh_objs: An argument list of mesh objects.
        :type  mesh_objs: MO list
        
        Returns: MO.
        ''' 
        
        if len(mesh_objs) > 1:
            return reduce(self.addmesh_merge, mesh_objs)
        else:
            raise ValueError('Must provide at least two objects to merge.')
            
    def create(self, name=None, mesh='tet', npoints=0, nelements=0):
        '''
        Create a Mesh Object
        
        Creates a mesh object in lagrit and an MO in the LaGriT object. Returns 
        the mesh object. 
        
        :kwarg name: Name to be given to the mesh object.
        :type  name: str
        
        :kwarg mesh: The type of mesh object to create.
        :type  mesh: str
        
        :kwarg npoints: The number of points.
        :type  npoints: int
        
        :kwarg nelements: The number of elements.
        :type  nelements: int
        
        Returns: MO
        '''
                        
        if type(name) is type(None):
            name = make_name('mo', self.mo.keys())     
        self.sendline('cmo/create/%s/%i/%i/%s'%(name, npoints, nelements, mesh))
        self.mo[name] = MO(name, self)
        return self.mo[name]
        
    def create_tet(self, name=None, npoints=0, nelements=0):
        '''Create a tetrahedron mesh object.'''
        return self.create(mesh='tet', **minus_self(locals()))
        
    def create_hex(self, name=None, npoints=0, nelements=0):
        '''Create a hexagon mesh object.'''
        return self.create(mesh='hex', **minus_self(locals()))
        
    def create_pri(self, name=None, npoints=0, nelements=0):
        '''Create a prism mesh object.'''
        return self.create(mesh='pri', **minus_self(locals()))  
            
    def create_pyr(self, name=None, npoints=0, nelements=0):
        '''Create a pyramid mesh object.'''
        return self.create(mesh='pyr', **minus_self(locals()))
        
    def create_tri(self, name=None, npoints=0, nelements=0):
        '''Create a triangle mesh object.'''
        return self.create(mesh='tri', **minus_self(locals()))
        
    def create_qua(self, name=None, npoints=0, nelements=0):
        '''Create a quadrilateral mesh object.'''
        return self.create(mesh='qua', **minus_self(locals())) 
             
    def create_hyb(self, name=None, npoints=0, nelements=0):
        '''Create a hybrid mesh object.'''
        return self.create(mesh='hyb', **minus_self(locals()))
        
    def create_line(self, npoints=0, mins=[], maxs=[], rz_switch=(0,0,0), name=None):
        '''Create a line mesh object.'''
        mo_new = self.create(mesh='lin', name=name, npoints=npoints)
        if len(mins) == 3 and len(maxs) == 3:
            mo_new.createpts_line(npoints,mins,maxs,rz_switch)
        return mo_new
        
    def create_triplane(self, name=None, npoints=0, nelements=0):
        '''Create a triplane mesh object.'''
        return self.create(mesh='triplane', **minus_self(locals()))
        
    def copy(self, mo, name=None):
        '''
        Copy Mesh Object
        
        Copies a mesh object, mo, and returns the MO object.
        '''
        
        #Check if name was specified, if not just generate one.
        if type(name) is type(None):
            name = make_name('mo', self.mo.keys())
        
        #Create the MO in lagrit and the PyLaGriT object.
        self.sendline('cmo/copy/%s/%s'%(name, str(mo)))
        self.mo[name] = MO(name, self)
        
        return self.mo[name]
    
class MO(object):
    ''' Mesh object class'''
    def __init__(self, name, parent):
        self.name = name
        self._parent = parent
        self.pset = {}
        self.eltset = {}
    def __repr__(self):
        return self.name
    def sendline(self,cmd):
        self._parent.sendline('cmo select '+self.name)
        self._parent.sendline(cmd)
    def status(self,brief=False):
        print self.name
        self._parent.cmo_status(self.name,brief=brief)
    def printatt(self,attname=None,stride=[1,0,0],pset=None,eltset=None,type='value'):
        stride = [str(v) for v in stride]
        if attname is None: attname = '-all-'
        if pset is None and eltset is None:
            cmd = '/'.join(['cmo/printatt',self.name,attname,type,','.join(stride)])
        else:
            if pset is not None:
                if isinstance(pset,PSet): setname = pset.name
                elif isinstance(pset,str): setname = pset
                else:
                    print "ERROR: PSet object or name of PSet object as a string expected for pset"
                    return
                cmd = '/'.join(['cmo/printatt',self.name,attname,type,','.join(['pset','get',setname])])
            if eltset is not None:
                if isinstance(eltset,EltSet): setname = eltset.name
                elif isinstance(eltset,str): setname = eltset
                else:
                    print "ERROR: EltSet object or name of EltSet object as a string expected for eltset"
                    return
                cmd = '/'.join(['cmo/printatt',self.name,attname,type,','.join(['eltset','get',setname])])
        self.sendline(cmd)
    def delatt(self,attnames,force=True):
        '''
        Delete a list of attributes

        :arg attnames: Attribute names to delete
        :type attnames: str or lst(str)
        :arg force: If true, delete even if the attribute permanent persistance
        :type force: bool

        '''
        # If single attribute as string, make list
        if isinstance(attnames,str): attnames = [attnames]
        for att in attnames:
            if force:
                cmd = '/'.join(['cmo/DELATT',self.name,att])
            else:
                cmd = '/'.join(['cmo/delatt',self.name,att])
            self.sendline(cmd)
    def addatt(self,attname,keyword=None,type='',rank='',length='',interpolate='',persistence='',ioflag='',value=''):
        '''
        Add a list of attributes

        :arg attnames: Attribute name to add
        :type attnames: str
        :arg keyword: Keyword used by lagrit for specific attributes
        :type name: str

        '''
        if keyword is not None:
            cmd = '/'.join(['cmo/addatt',self.name,keyword,attname])
        else:
            cmd = '/'.join(['cmo/addatt',self.name,attname,rank,length,interpolate,persistence,ioflag,value])
        self.sendline(cmd)
    def addatt_voronoi_volume(self,name='voronoi_volume'):
        '''
        Add voronoi volume attribute to mesh object

        :arg name: name of attribute in LaGriT
        :type name: str
        '''
        self.addatt(name,keyword='voronoi_volume')
    def minmax(self,attname=None,stride=[1,0,0],pset=None):
        self.printatt(attname=attname,stride=stride,pset=None,type='minmax')
    def list(self,attname=None,stride=[1,0,0],pset=None):
        self.printatt(attname=attname,stride=stride,pset=pset,type='list')
    def setatt(self,attname,value,stride=[1,0,0]):
        stride = [str(v) for v in stride]
        cmd = '/'.join(['cmo/setatt',self.name,attname,','.join(stride),str(value)])
        self.sendline(cmd)
        
    def pset_geom(
            self, mins, maxs, 
            ctr=(0,0,0), geom='xyz', stride=(1,0,0), name=None
        ):
        '''
        Define PSet by Geometry
        
        Selects points from geomoetry specified by string geom and returns a 
        PSet.
        
        :arg  mins: Coordinate of one of the shape's defining points.
                     xyz (Cartesian):   (x1, y1, z1); 
                     rtz (Cylindrical): (radius1, theta1, z1);
                     rtp (Spherical):   (radius1, theta1, phi1);
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Coordinate of one of the shape's defining points.
                     xyz (Cartesian):   (x2, y2, z2); 
                     rtz (Cylindrical): (radius2, theta2, z2);
                     rtp (Spherical):   (radius2, theta2, phi2);
        :type maxs: tuple(int, int, int)
        
        :kwarg ctr: Coordinate of the relative center.
        :type  ctr: tuple(int, int, int)
        
        :kwarg geom: Type of geometric shape: 'xyz' (spherical), 
                     'rtz' (cylindrical), 'rtp' (spherical)
        :type  geom: str
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        Returns: PSet object
        '''
        
        if name is None:
            name = make_name('p',self.pset.keys())
            
        mins = [str(v) for v in mins]
        maxs = [str(v) for v in maxs]
        stride = [str(v) for v in stride]
        center = [str(v) for v in ctr]
        
        cmd = '/'.join(['pset', name, 'geom', geom, ','.join(stride),
                        ','.join(mins),','.join(maxs), ','.join(center)])
        self.sendline(cmd)
        self.pset[name] = PSet(name, self)
        
        return self.pset[name]

    def pset_geom_xyz(self, mins, maxs, ctr=(0,0,0), stride=(1,0,0), name=None):
        '''
        Define PSet by Tetrahedral Geometry
        
        Selects points from a Tetrahedral region.
        
        :arg  mins: Coordinate point of 1 of the tetrahedral's corners. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Coordinate point of 1 of the tetrahedral's corners.
        :type maxs: tuple(int, int, int)
        
        :kwarg ctr: Coordinate of the relative center.
        :type  ctr: tuple(int, int, int)
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        Returns: PSet object
        '''
        return self.pset_geom(geom='xyz', **minus_self(locals()))

    def pset_geom_rtz(self, mins, maxs, ctr=(0,0,0), stride=(1,0,0), name=None):
        '''
        Define PSet by Cylydrical Geometry
        
        Selects points from a Tetrahedral region.
        
        :arg  mins: Defines radius1, theta1, and z1. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Defines radius2, theta2, and z2.
        :type maxs: tuple(int, int, int)
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        :kwarg ctr: Coordinate of the relative center.
        :type  ctr: tuple(int, int, int)
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        Returns: PSet object
        '''
        return self.pset_geom(geom='rtz', **minus_self(locals()))
        
    def pset_geom_rtp(self, mins, maxs, ctr=(0,0,0), stride=(1,0,0), name=None):
        '''
        Define PSet by Cylydrical Geometry
        
        Selects points from a Tetrahedral region.
        
        :arg  mins: Defines radius1, theta1, and phi1. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Defines radius2, theta2, and phi2.
        :type maxs: tuple(int, int, int)
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        :kwarg ctr: Coordinate of the relative center.
        :type  ctr: tuple(int, int, int)
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        Returns: PSet object
        '''
        return self.pset_geom(geom='rtp', **minus_self(locals()))
        
    def pset_attribute(self, attribute,value,comparison='eq',stride=(1,0,0), name=None):
        '''
        Define PSet by attribute 
        
        :kwarg attribute: Nodes defined by attribute ID.
        :type  attribute: str
        
        :kwarg value: attribute ID value.
        :type  value: integer
        
        :kwarg comparison: attribute comparison, default is eq.
        :type  comparison: can use default without specifiy anything, or list[lt|le|gt|ge|eq|ne] 
        
        :kwarg stride: Nodes defined by ifirst, ilast, and istride.
        :type  stride: list[int, int, int]
        
        :kwarg name: The name to be assigned to the PSet created.
        :type  name: str
        
        Returns: PSet object
        '''
        if name is None:
            name = make_name('p',self.pset.keys())
            
        stride = [str(v) for v in stride]
        
        cmd = '/'.join(['pset', name, 'attribute', attribute, ','.join(stride),
                        str(value),comparison])
        self.sendline(cmd)
        self.pset[name] = PSet(name, self)

        return self.pset[name]

    def resetpts_itp(self):
        '''
        set node type from connectivity of mesh 
        
        '''
        self.sendline('resetpts/itp')

    def eltset_object(self, mo, name=None):
        '''
        Create element set from the intersecting elements with another mesh object
        '''
        if name is None:
            name = make_name('e',self.eltset.keys())
        attr_name = self.intersect_elements(mo)
        e_attr = self.eltset_attribute(attr_name,0,boolstr='gt')
        self.eltset[name] = EltSet(name,self)
        return self.eltset[name]
    def eltset_bool(self, eset_list, boolstr='union', name=None):
        '''
        Create element set from boolean operation of set of element sets

        :arg eset_list: List of elements to perform boolean operation on
        :type eset_list: lst(PyLaGriT element set)
        :arg boolstr: type of boolean operation to perform on element sets, one of [union,inter,not]
        :type boolstr: str
        :arg name: The name to be assigned to the EltSet within LaGriT
        :type name: str
        :returns: PyLaGriT element set object
        '''
        if name is None:
            name = make_name('e',self.eltset.keys())
        cmd = ['eltset',name,boolstr,' '.join([e.name for e in eset_list])]
        self.sendline('/'.join(cmd))
        self.eltset[name] = EltSet(name,self)
        return self.eltset[name]
    def eltset_region(self,region,name=None):
        if name is None:
            name = make_name('e',self.eltset.keys())
        if isinstance(region,Region): region_name = region.name
        elif isinstance(region,str): region_name = region
        else:
            print 'region must be a string or object of class Region'
            return
        cmd = '/'.join(['eltset',name,'region',region_name])
        self.sendline(cmd)
        self.eltset[name] = EltSet(name,self)
        return self.eltset[name]
    def eltset_attribute(self,attribute_name,attribute_value,boolstr='eq',name=None):
        if name is None:
            name = make_name('e',self.eltset.keys())
        cmd = '/'.join(['eltset',name,attribute_name,boolstr,str(attribute_value)])
        self.sendline(cmd)
        self.eltset[name] = EltSet(name,self)
        return self.eltset[name]
    def rmpoint_pset(self,pset,itype='exclusive',compress=True,resetpts_itp=True):
        if isinstance(pset,PSet): name = pset.name
        elif isinstance(pset,str): name = pset
        else:
            print 'p must be a string or object of class PSet'
            return
        cmd = 'rmpoint/pset,get,'+name+'/'+itype
        self.sendline(cmd)
        if compress: self.rmpoint_compress(resetpts_itp=resetpts_itp)
    def rmpoint_eltset(self,eltset,compress=True,resetpts_itp=True):
        if isinstance(eltset,EltSet): name = eltset.name
        elif isinstance(eltset,str): name = eltset
        else:
            print 'eltset must be a string or object of class EltSet'
            return
        cmd = 'rmpoint/element/eltset,get,'+name
        self.sendline(cmd)
        if compress: self.rmpoint_compress(resetpts_itp=resetpts_itp)
    def rmpoint_compress(self,filter_bool=False,resetpts_itp=True):
        '''
        remove all marked nodes and correct the itet array 

        :param resetpts_itp: set node type from connectivity of mesh
        :type resetpts_itp: bool

        '''

        if filter_bool: self.sendline('filter/1,0,0')
        self.sendline('rmpoint/compress')
        if resetpts_itp: self.resetpts_itp()
    def reorder_nodes(self, order='ascending',cycle='zic yic xic'):
        self.sendline('resetpts itp')
        self.sendline('/'.join(['sort',self.name,'index',order,'ikey',cycle]))
        self.sendline('reorder / '+self.name+' / ikey')
        self.sendline('cmo / DELATT / '+self.name+' / ikey')
    def gmv(self,exe=None,filename=None):
        if filename is None: filename = self.name+'.gmv'
        if exe is not None: self._parent.gmv_exe = exe
        self.sendline('dump/gmv/'+filename+'/'+self.name)
        os.system(self._parent.gmv_exe+' -i '+filename)
    def paraview(self,exe=None,filename=None):
        if filename is None: filename = self.name+'.inp'
        if exe is not None: self._parent.paraview_exe = exe
        self.sendline('dump/avs/'+filename+'/'+self.name)
        os.system(self._parent.paraview_exe+' '+filename)
    def dump(self,filename=None,format=None,*args):
        if filename is None and format is None:
            print "Error: At least one of either filename or format option is required"
            return
        #if format is not None: cmd = '/'.join(['dump',format])
        #else: cmd = 'dump'
        if filename and format: 
            if format in ['fehm','zone_outside','zone_outside_minmax']: filename = filename.split('.')[0]
            if format is 'stor' and len(args)==0: filename = filename.split('.')[0]
            cmd = '/'.join(['dump',format,filename,self.name])
        elif format: 
            if format in ['avs','avs2']: filename = self.name+'.inp'
            elif format is 'fehm': filename = self.name
            elif format is 'gmv': filename = self.name+'.gmv'
            elif format is 'tecplot': filename = self.name+'.plt'
            elif format is 'lagrit': filename = self.name+'.lg'
            elif format is 'exo': filename = self.name+'.exo'
            cmd = '/'.join(['dump',format,filename,self.name])
        else:
            cmd = '/'.join(['dump',filename,self.name])
        for arg in args: cmd = '/'.join([cmd,str(arg)])
        self.sendline(cmd)
    def dump_avs2(self,filename,points=True,elements=True,node_attr=True,element_attr=True):
        '''
        Dump avs file

        :arg filename: Name of avs file
        :type filename: str
        :arg points: Output point coordinates
        :type points: bool
        :arg elements: Output connectivity
        :type elements: bool
        :arg node_attr: Output node attributes
        :type node_attr: bool
        :arg element_attr: Output element attributes
        :type element_attr: bool
        '''
        self.dump(filename,'avs2',int(points),int(elements),int(node_attr),int(element_attr))
    def dump_exo(self,filename,psets=False,eltsets=False,facesets=[]):
        cmd = '/'.join(['dump/exo',filename,self.name])
        if psets: cmd = '/'.join([cmd,'psets'])
        else: cmd = '/'.join([cmd,' '])
        if eltsets: cmd = '/'.join([cmd,'eltsets'])
        else: cmd = '/'.join([cmd,' '])
        if len(facesets):
            cmd = '/'.join([cmd,'facesets'])
            for fc in facesets: 
                cmd += ' &\n'+fc.filename
        self.sendline(cmd)
    def dump_gmv(self,filename,format='binary'):
        self.dump(filename,'gmv',format)
    def dump_fehm(self,filename):
        self.dump(filename,'fehm')
    def dump_lg(self,filename,format='binary'):
        self.dump(filename,'lagrit',format)
    def delete(self):
        self.sendline('cmo/delete/'+self.name)
    
    def createpts_line(self, npts, mins, maxs, rz_switch=(0,0,0)):
        '''
        Create and Connect Points in a line
        
        :arg  npts: The number of points to create in line
        :type npts: int
        :arg  mins: The starting value for each dimension.
        :type mins: tuple(int, int, int)
        :arg  maxs: The ending value for each dimension.
        :type maxs: tuple(int, int, int)
        :kwarg rz_switch: Determines true or false (1 or 0) for using ratio zoning values.  
        :type  rz_switch: tuple(int, int, int)
        
        '''
        
        mins = [str(v) for v in mins]
        maxs = [str(v) for v in maxs]
        rz_switch = [str(v) for v in rz_switch]

        cmd = '/'.join(['createpts','line',str(npts),' ',' ',','.join(mins+maxs),','.join(rz_switch)])
        self.sendline(cmd)
    def createpts_brick(
            self, crd, npts, mins, maxs,  
            ctr=(1,1,1), rz_switch=(0,0,0), rz_vls=(1,1,1)
        ):
        '''
        Create and Connect Points
        
        Creates a grid of points in the mesh object and connects them. 
        
        :arg crd: Coordinate type of either 'xyz' (cartesian coordinates), 
                    'rtz' (cylindrical coordinates), or 
                    'rtp' (spherical coordinates).
        :type  crd: str
        
        :arg  npts: The number of points to create in each dimension.
        :type npts: tuple(int, int, int)
        
        :arg  mins: The starting value for each dimension.
        :type mins: tuple(int, int, int)
        
        :arg  maxs: The ending value for each dimension.
        :type maxs: tuple(int, int, int)
        
        :kwarg ctr: Defines the center of each cell. For 0, points are placed in
                    the middle of each cell. For 1, points are placed at the 
                    edge of each cell.
        :type  ctr: tuple(int, int, int)

        :kwarg rz_switch: Determines true or false (1 or 0) for using ratio 
                          zmoning values.  
        :type  rz_switch: tuple(int, int, int)
        
        :kwarg rz_vls: Ratio zoning values. Each point will be multiplied by
                       a scale of the value for that dimension.
        :type  rz_vls: tuple(int, int, int)
        '''
        
        ni, nj, nk = map(str, npts)
        mins = [float(v) for v in mins]
        maxs = [float(v) for v in maxs]
        xmn, ymn, zmn = map(str, mins)
        xmx, ymx, zmx = map(str, maxs)
        iiz, ijz, ikz = map(str, ctr)
        iirat, ijrat, ikrat = map(str, rz_switch)
        xrz, yrz, zrz = map(str, rz_vls)

        t = (crd, ni, nj, nk, xmn, ymn, zmn, xmx, ymx, zmx) 
        t = t + (iiz, ijz, ikz, iirat, ijrat, ikrat, xrz, yrz, zrz)
        cmd = 'createpts/brick/%s/%s,%s,%s/%s,%s,%s/%s,%s,%s/%s,%s,%s/'+\
              '%s,%s,%s/%s,%s,%s'
        self.sendline(cmd%t)

    def createpts_brick_xyz(
            self, npts, mins, maxs, 
            ctr=(1,1,1), rz_switch=(0,0,0), rz_vls=(1,1,1)):
        '''Create and connect Cartesian coordinate points.'''
        self.createpts_brick('xyz', **minus_self(locals()))
        
    def createpts_brick_rtz(
            self, npts, mins, maxs, 
            ctr=(1,1,1), rz_switch=(0,0,0), rz_vls=(1,1,1)):
        '''Create and connect cylindrical coordinate points.'''
        self.createpts_brick('rtz', **minus_self(locals()))
        
    def createpts_brick_rtp(
            self, npts, mins, maxs, 
            ctr=(1,1,1), rz_switch=(0,0,0), rz_vls=(1,1,1)):
        '''Create and connect spherical coordinates.'''
        self.createpts_brick(ntps, **minus_self(locals()))
        
    def pset_not(self, ps, name=None):
        '''
        Return PSet from Logical Not
        
        Defines and returns a PSet from points that are not inside the PSet, ps.
        '''
        
        #Generated a name if one is not specified.
        if name is None:
            name = make_name('p',self.pset.keys())
        
        #Create the new PSET in lagrit and the pylagrit object.
        cmd = 'pset/%s/not/%s'%(name, str(ps))
        self.sendline(cmd)
        self.pset[name] = PSet(name, self)
        
        return self.pset[name]
        
    def subset(self, mins, maxs, geom='xyz'):
        '''
        Return Mesh Object Subset
        
        Creates a new mesh object that contains only a geometric subset defined
        by mins and maxs. 
        
        :arg  mins: Coordinate of one of the shape's defining points.
                     xyz (Cartesian):   (x1, y1, z1); 
                     rtz (Cylindrical): (radius1, theta1, z1);
                     rtp (Spherical):   (radius1, theta1, phi1);
        :typep mins: tuple(int, int, int)
        
        :arg  maxs: Coordinate of one of the shape's defining points.
                     xyz (Cartesian):   (x2, y2, z2); 
                     rtz (Cylindrical): (radius2, theta2, z2);
                     rtp (Spherical):   (radius2, theta2, phi2);
        :type maxs: tuple(int, int, int)
        
        :kwarg geom: Type of geometric shape: 'xyz' (spherical), 
                     'rtz' (cylindrical), 'rtp' (spherical)
        :type  geom: str
        
        Returns: MO object
        '''
        
        lg = self._parent
        new_mo = lg.copy(self)
        sub_pts = new_mo.pset_geom(mins, maxs, geom=geom)
        rm_pts = new_mo.pset_not(sub_pts)
        
        new_mo.rmpoint_pset(rm_pts)
        return new_mo
        
    def subset_xyz(self, mins, maxs):
        '''
        Return Tetrehedral MO Subset
        
        Creates a new mesh object that contains only a tetrehedral subset 
        defined by mins and maxs. 
        
        :arg  mins: Coordinate point of 1 of the tetrahedral's corners. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Coordinate point of 1 of the tetrahedral's corners.
        :type maxs: tuple(int, int, int)
        
        Returns: MO object
        '''
        return self.subset(geom='xyz', **minus_self(locals()))
        
    def subset_rtz(self, mins, maxs):
        '''
        Return Cylindrical MO Subset
        
        Creates a new mesh object that contains only a cylindrical subset 
        defined by mins and maxs. 
        
        :arg  mins: Defines radius1, theta1, and z1. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Defines radius2, theta2, and z2.
        :type maxs: tuple(int, int, int)
        
        Returns: MO object
        '''
        return self.subset(geom='rtz', **minus_self(locals()))
        
    def subset_rtp(self, mins, maxs):
        '''
        Return Spherical MO Subset
        
        Creates a new mesh object that contains only a spherical subset 
        defined by mins and maxs. 
        
        :arg  mins: Defines radius1, theta1, and phi1. 
        :type mins: tuple(int, int, int)
        
        :arg  maxs: Defines radius2, theta2, and phi2.
        :type maxs: tuple(int, int, int)
        
        Returns: MO object
        '''
        return self.subset(geom='rtp', **minus_self(locals()))

    def grid2grid(self, ioption, name=None):
        '''
        Convert a mesh with one element type to a mesh with another
        
        :arg ioption: type of conversion:
            quadtotri2   quad to 2 triangles, no new points. 
            prismtotet3   prism to 3 tets, no new points. 
            quadtotri4   quad to 4 triangles, with one new point. 
            pyrtotet4   pyramid to 4 tets, with one new point. 
            hextotet5   hex to 5 tets, no new points. 
            hextotet6   hex to 6 tets, no new points. 
            prismtotet14   prism to 14 tets, four new points (1 + 3 faces). 
            prismtotet18   prism to 18 tets, six new points (1 + 5 faces). 
            hextotet24   hex to 24 tets, seven new points (1 + 6 faces). 
            tree_to_fe   quadtree or octree grid to grid with no parent-type elements. 
        :type option: str
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''
        if name is None: name = make_name('mo',self._parent.mo.keys())
        cmd = '/'.join(['grid2grid',ioption,name,self.name])
        self.sendline(cmd)
        self._parent.mo[name] = MO(name,self._parent)
        return self._parent.mo[name]
    def grid2grid_tree_to_fe(self, name=None):
        '''
        Quadtree or octree grid to grid with no parent-type elements. 
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='tree_to_fe', **minus_self(locals()))
    def grid2grid_quadtotri2(self, name=None):
        '''
        Quad to 2 triangles, no new points. 
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='quadtotri2', **minus_self(locals()))
    def grid2grid_prismtotet3(self, name=None):
        '''
        Quad to 2 triangles, no new points. 
        Prism to 3 tets, no new points. 
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='quadtotri3', **minus_self(locals()))
    def grid2grid_quadtotri4(self, name=None):
        '''
        Quad to 4 triangles, with one new point
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='quadtotri4', **minus_self(locals()))
    def grid2grid_pyrtotet4(self, name=None):
        '''
        Pyramid to 4 tets, with one new point
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='pyrtotet4', **minus_self(locals()))
    def grid2grid_hextotet5(self, name=None):
        '''
        Hex to 5 tets, no new points
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='hextotet5', **minus_self(locals()))
    def grid2grid_hextotet6(self, name=None):
        '''
        Hex to 6 tets, no new points
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='hextotet6', **minus_self(locals()))
    def grid2grid_prismtotet14(self, name=None):
        '''
        Prism to 14 tets, four new points (1 + 3 faces)
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='prismtotet14', **minus_self(locals()))
    def grid2grid_prismtotet18(self, name=None):
        '''
        Prism to 18 tets, four new points (1 + 3 faces)
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='prismtotet18', **minus_self(locals()))
    def grid2grid_hextotet24(self, name=None):
        '''
        Hex to 24 tets, seven new points (1 + 6 faces)
        :arg name: Internal Lagrit name of new mesh object, automatically created if None
        :type name: str

        Returns MO object
        '''        
        return self.grid2grid(ioption='hextotet24', **minus_self(locals()))
    def connect(self, option1, option2=None, stride=None, big_tet_coords=[]):
        '''
        Connect the nodes into a Delaunay tetrahedral or triangle grid.
        
        :arg option1: type of connect: delaunay, noadd, or check_interface
        :type option: str
        :arg option2: type of connect: noadd, or check_interface
        :type option: str
        :arg stride: tuple of (first, last, stride) of points
        :type stride: tuple(int)
        '''
        cmd = ['connect',option1]
        if stride is not None and option is 'delaunay': 
            stride = [str(v) for v in stride]
            cmd += [','.join(stride)]
            for b in big_tet_coords:
                bs = [str(v) for v in b]
                cmd += [','.join(bs)]
        if option2 is not None:
                cmd += [option2]
        cmd = '/'.join(cmd)
        self.sendline(cmd)
    def connect_delaunay(self, option2=None, stride=None, big_tet_coords=[]):
        '''
        Connect the nodes into a Delaunay tetrahedral or triangle grid without adding nodes.
        '''
        mo_tmp = self.copypts()
        mo_tmp.setatt('imt',1)
        mo_tmp.setatt('itp',0)
        mo_tmp.rmpoint_compress(filter_bool=True)
        mo_tmp.connect(option1='delaunay', option2=option2,stride=stride,big_tet_coords=big_tet_coords)
        self.sendline('/'.join(['cmo','delete',self.name]))
        self.sendline('/'.join(['cmo','move',self.name,mo_tmp.name]))
        mo_tmp.delete()
        #self.connect(option1='delaunay', **minus_self(locals()))
    def connect_noadd(self):
        '''
        Connect the nodes into a Delaunay tetrahedral or triangle grid without adding nodes.
        '''
        self.connect(option1='noadd')
    def connect_check_interface(self):
        '''
        Connect the nodes into a Delaunay tetrahedral or triangle grid
        exhaustively checking that no edges of the mesh cross a material
        boundary.
        '''
        self.connect(option1='check_interface')
    def copypts(self, name=None):
        '''
        Copy points from mesh object to new mesh object

        :arg name: Name to use within lagrit for the created mesh object
        :type name: str
        :returns: mesh object
        '''
        if name is None: name = make_name('mo',self._parent.mo.keys())
        mo_new = self._parent.create_tet()
        self.sendline('/'.join(['copypts',mo_new.name,self.name]))
        return mo_new
    def extrude(self, offset, offset_type='const', return_type='volume', direction=[], name=None):
        '''
        Extrude mesh object to new mesh object
        This command takes the current mesh object (topologically 1d or 2d mesh (a line, a set of line 
        segments, or a planar or non-planar surface)) and extrudes it into three 
        dimensions along either the normal to the curve or surface (default), 
        along a user defined vector, or to a set of points that the user has specified.
        If the extrusion was along the normal of the surface or along a user 
        defined vector, the command can optionally find the external surface of 
        the volume created and return that to the user.
        Refer to http://lagrit.lanl.gov/docs/commands/extrude.html for more details on arguments.


        :arg name: Name to use within lagrit for the created mesh object
        :type name: str
        :arg offset: Distance to extrude
        :type offset: float
        :arg offset_type: either const or min (interp will be handled in the PSET class in the future)         
        :type offset_type: str
        :arg return_type: either volume for entire mesh or bubble for just the external surface
        :type return_type: str
        :arg direction: Direction to extrude in, defaults to normal of the object
        :type direction: lst[float,float,float]
        :returns: mesh object
        '''
        if name is None: name = make_name('mo',self._parent.mo.keys())
        cmd = ['extrude',name,self.name,offset_type,str(offset),return_type]
        if len(direction) == 3: cmd.append(','.join([str(v) for v in direction]))
        self.sendline('/'.join(cmd))
        self._parent.mo[name] = MO(name, self._parent)
        return self._parent.mo[name]
    def refine_to_object(self, mo, level=None, imt=None, prd_choice=None):
        '''
        Refine mesh at locations that intersect another mesh object

        :arg mo: Mesh object to intersect with current mesh object to determine where to refine
        :type mo: PyLaGriT mesh object
        :arg level: max level of refinement
        :type level: int
        :arg imt: Value to assign to imt (LaGriT material type attribute)
        :type imt: int
        :arg prd_choice: directions of refinement
        :type prd_choice: int
        '''

        if level is None: level = 1; itetlevbool = False
        for i in range(level):
            attr_name = self.intersect_elements(mo)
            if itetlevbool:
                e_attr = self.eltset_attribute(attr_name,0,boolstr='gt')
                e_level = self.eltset_attribute('itetlev',level,boolstr='lt')
                e_refine = self.eltset_bool( [e_attr,e_level], boolstr='inter' )
                e_attr.delete()
                e_level.delete()
            else:
                e_refine = self.eltset_attribute(attr_name,0,boolstr='gt')
            if prd_choice is not None:
                p_refine = e_refine.pset()
                p_refine.refine(prd_choice=prd_choice)
                p_refine.delete()
            else:
                e_refine.refine()
            e_refine.delete()
        if imt is not None: 
            attr_name = self.intersect_elements(mo)
            e_attr = self.eltset_attribute(attr_name,0,boolstr='gt')
            p = e_attr.pset()
            p.setatt('imt',13)
            p.delete()
        

    def intersect_elements(self, mo, attr_name='attr00'):
        '''
        This command takes two meshes and creates an element-based attribute in mesh1 
        that contains the number of elements in mesh2 that intersected the respective 
        element in mesh1. We define intersection as two elements sharing any common point.
        
        :arg mo: Mesh object to intersect with current mesh object to determine where to refine
        :type mo: PyLaGriT mesh object
        :arg attr_name: Name to give created attribute 
        :type attr_name: str
        :returns: attr_name
        '''
        self.sendline('/'.join(['intersect_elements',self.name,mo.name,attr_name]))
        return attr_name
    def extract_surfmesh(self,name=None,stride=[1,0,0],reorder=False):
        return self._parent.extract_surfmesh( cmo_in=self )



 
class Surface(object):
    ''' Surface class'''
    def __init__(self, name, parent):
        self.name = name
        self._parent = parent
    def __repr__(self):
        return self.name
    def release(self):
        cmd = 'surface/'+self.name+'/release'
        self._parent.sendline(cmd)
        del self._parent.surface[self.name]

class PSet(object):
    ''' Pset class'''
    def __init__(self, name, parent):
        self.name = name
        self._parent = parent
    def __repr__(self):
        return str(self.name)
    def delete(self):
        cmd = 'pset/'+self.name+'/delete'
        self._parent.sendline(cmd)
        del self._parent.pset[self.name]
    def minmax(self,attname=None,stride=[1,0,0]):
        self._parent.printatt(attname=attname,stride=stride,pset=self.name,type='minmax')
    def list(self,attname=None,stride=[1,0,0]):
        self._parent.printatt(attname=attname,stride=stride,pset=self.name,type='list')
    def setatt(self,attname,value):
        cmd = '/'.join(['cmo/setatt',self._parent.name,attname,'pset get '+self.name,str(value)])
        self._parent.sendline(cmd)
    def refine(self,refine_type='element',refine_option='constant',interpolation=' ',prange=[-1,0,0],field=' ',inclusive_flag='exclusive',prd_choice=None):
        prange = [str(v) for v in prange]
        if prd_choice is None:
            cmd = '/'.join(['refine',refine_option,field,interpolation,refine_type,'pset get '+self.name,','.join(prange),inclusive_flag])
        else:
            cmd = '/'.join(['refine',refine_option,field,interpolation,refine_type,'pset get '+self.name,','.join(prange),inclusive_flag,'amr '+str(prd_choice)])
        self._parent.sendline(cmd)
    def eltset(self,membership='inclusive',name=None):
        '''
        Create eltset from pset

        :arg membership: type of element membership, one of [inclusive,exclusive,face]
        :type membership: str
        :arg name: Name of element set to be used within LaGriT
        :type name: str
        :returns: PyLaGriT EltSet object
        '''
        if name is None: name = make_name('e',self._parent.eltset.keys())
        cmd = ['eltset',name,membership,'pset','get',self.name]
        self._parent.sendline('/'.join(cmd))
        self._parent.eltset[name] = EltSet(name,self._parent)
        return self._parent.eltset[name]
    def expand(self,membership='inclusive'):
        '''
        Add points surrounding pset to pset

        :arg membership: type of element membership, one of [inclusive,exclusive,face]
        :type membership: str
        '''
        e = self.eltset(membership=membership)
        self._parent.sendline('pset/'+self.name+'/delete')
        self = e.pset(name=self.name)


class EltSet(object):
    ''' EltSet class'''
    def __init__(self, name, parent):
        self.name = name
        self.faceset = None
        self._parent = parent
    def __repr__(self):
        return str(self.name)
    def delete(self):
        cmd = 'eltset/'+self.name+'/delete'
        self._parent.sendline(cmd)
        del self._parent.eltset[self.name]
    def create_faceset(self,filename=None,reorder=True):
        if filename is None:
            filename = make_name( 'faceset', self.facesets.keys() )
        motmpnm = make_name( 'mo_tmp',self._parent._parent.mo.keys() )
        self._parent._parent.sendline('/'.join(['cmo/copy',motmpnm,self._parent.name]))
        self._parent._parent.sendline('/'.join(['cmo/DELATT',motmpnm,'itetclr0']))
        self._parent._parent.sendline('/'.join(['cmo/DELATT',motmpnm,'itetclr1']))
        self._parent._parent.sendline('/'.join(['cmo/DELATT',motmpnm,'facecol']))
        self._parent._parent.sendline('/'.join(['cmo/DELATT',motmpnm,'idface0']))
        self._parent._parent.sendline('/'.join(['cmo/DELATT',motmpnm,'idelem0']))
        self._parent._parent.sendline('eltset / eall / itetclr / ge / 0')
        self._parent._parent.sendline('eltset/edel/not eall '+self.name)
        self._parent._parent.sendline('rmpoint / element / eltset get edel')
        self._parent._parent.sendline('rmpoint / compress')
        self._parent._parent.sendline('/'.join(['dump / avs2',filename,motmpnm,'0 0 0 2']))
        self._parent._parent.sendline('cmo / delete /'+motmpnm)
        self.faceset = FaceSet(filename,self)
        return self.faceset
    def minmax(self,attname=None,stride=[1,0,0]):
        self._parent.printatt(attname=attname,stride=stride,eltset=self.name,type='minmax')
    def list(self,attname=None,stride=[1,0,0]):
        self._parent.printatt(attname=attname,stride=stride,eltset=self.name,type='list')
    def refine(self):
        cmd = '/'.join(['refine','eltset','eltset,get,'+self.name])
        self._parent.sendline(cmd)
    def pset(self,name=None):
        '''
        Create a pset from the points in an element set
        :arg name: Name of point set to be used within LaGriT
        :type name: str
        :returns: PyLaGriT PSet object
        '''
        if name is None: name = make_name('p',self._parent.pset.keys())
        cmd = '/'.join(['pset',name,'eltset',self.name])
        self._parent.sendline(cmd)
        self._parent.pset[name] = PSet(name, self._parent)
        return self._parent.pset[name]
    def setatt(self,attname,value):
        cmd = '/'.join(['cmo/setatt',self._parent.name,attname,'eltset, get,'+self.name,str(value)])
        self._parent.sendline(cmd)

class Region(object):
    ''' Region class'''
    def __init__(self, name, parent):
        self.name = name
        self._parent = parent
    def __repr__(self):
        return str(self.name)

class FaceSet(object):
    ''' FaceSet class'''
    def __init__(self, filename, parent):
        self.filename = filename
        self._parent = parent
    def __repr__(self):
        return str(self.filename)

def make_name( base, names ):
    i = 1
    name = base+str(i)
    while name in names:
        i += 1
        name = base+str(i)
    return name 
    
def minus_self(kvpairs):
    del kvpairs['self']
    return kvpairs






