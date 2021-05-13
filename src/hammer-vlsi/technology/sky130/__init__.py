#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Skywater plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
#import tempfile
import shutil
#from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

from hammer_tech import HammerTechnology
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, TCLTool, HammerToolHookAction

class SkywaterTech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        try:
            import gdspy  # type: ignore
        except ImportError:
            self.logger.error("Couldn't import gdspy Python package, needed to merge Skywater gds.")
            shutil.rmtree(self.cache_dir)
            sys.exit()
        # make cache directories for all necessary lib files
        #dirs = 'cdl gds lef lib verilog/models'.split()
        dir = 'gds'#for dir in dirs:
        os.makedirs(os.path.join(self.cache_dir,dir), exist_ok=True)
        # make models dirs in parse_models function
        
        # useful paths/values
        base_dir = self.get_setting("technology.sky130.skywater_pdk")
        libraries = os.listdir(base_dir+'/libraries/')
        library = 'sky130_fd_sc_hd'
        libs_path = base_dir+'/libraries/'
        lib_path = libs_path+library+'/latest/'
        cells = os.listdir(lib_path+'/cells')
        
        self.combine_gds(lib_path,library,cells)
        #self.combine_lef(lib_path,library,cells)
        #self.combine_verilog(lib_path,library,cells)
        #self.parse_models(lib_path,library)
        #self.combine_cdl(lib_path,library,cells)
        #self.lib_setup(lib_path,library)
        
    def lib_setup(self,lib_path,library) -> None:
        # set up file
        corners = os.listdir(os.path.join(lib_path,'timing'))
        # find ccsnoise corners
        ccsnoise_corners = []
        for corner in corners:
            if corner.endswith('_ccsnoise.lib'):
                corner = corner.replace('_ccsnoise','')
                ccsnoise_corners.append(corner)
        for corner in corners:
            if corner.endswith('_ccsnoise.lib'):
                continue
            # remove ccsnoise info
            if corner in ccsnoise_corners:
                f = open(os.path.join(self.cache_dir,'lib',corner), 'w')
                lib_file = open(os.path.join(lib_path,'timing',corner),'r')
                count = 0; # count brackets :(
                ccsn = False
                for line in lib_file:
                    if ( ('ccsn_first_stage' in line) or ('ccsn_last_stage' in line) ):
                        ccsn = True
                    if (not ccsn):
                        f.write(line)
                    else:
                        count = count + line.count('{')
                        count = count - line.count('}')
                        if count == 0:
                            ccsn = False
                f.close()
            # copy rest of lib files to tech cache
            elif corner.endswith('.lib'):
                shutil.copyfile(os.path.join(lib_path,'timing',corner),os.path.join(self.cache_dir,'lib',corner))
        
    def combine_gds(self,lib_path,library,cells) -> None:
        import gdspy
        # create new gds lib
        gds_lib = gdspy.GdsLibrary()
        # iterate over all cells
        for cell in cells:
            cell_path = os.path.join(lib_path,'cells',cell)
            cell_files = os.listdir(cell_path)
            # iterate over all gds files for each cell
            for cell_file in cell_files:
                if cell_file.endswith('.gds'):
                    cell_gds_path = os.path.join(cell_path,cell_file)
                    # import gds file into gds library
                    cell_gds = gds_lib.read_gds(cell_gds_path)
        gds_lib_path = os.path.join(self.cache_dir,'gds',library+'.gds')
        gds_lib.write_gds(gds_lib_path)
        
    def combine_lef(self,lib_path,library,cells) -> None:
        # set up file
        f = open(os.path.join(self.cache_dir,"lef",library+".lef"), "w")
        f.write('VERSION 5.6 ;\nNAMESCASESENSITIVE ON ;\nBUSBITCHARS "[]" ;\nDIVIDERCHAR "/" ;\n\n')
        # iterate over cells
        for cell in cells:
            cell_path = os.path.join(lib_path,'cells',cell)
            cell_files = os.listdir(cell_path)
            for cell_file in cell_files:
                if cell_file.endswith('.lef') and not cell_file.endswith('magic.lef'):
                    cell_file = open(os.path.join(cell_path,cell_file),"r")
                    writing=False
                    for line in cell_file:
                        if line.startswith("END LIBRARY"): 
                          f.write('\n\n')
                          break
                        if line.startswith("MACRO"):
                          writing=True
                        if writing:
                          f.write(line)
        f.close()
    
    def combine_verilog2(self,lib_path,library,cells) -> None:
        # set up file
        f = open(os.path.join(self.cache_dir,"verilog",library+".v"), "w")
        #f.write('`define UNIT_DELAY  \n') # WHERE TF IS THIS DEFINED IN PDK?!?!?!
        # include udp models
        models = os.listdir(os.path.join(lib_path,'models'))
        for model in models:
            model_path = os.path.join(self.cache_dir,'verilog','models',library+'__'+model+'.v')
            f.write('`include "'+model_path+'"\n')
        # iterate over cells
        for cell in cells:
            cell_path = os.path.join(lib_path,'cells',cell)
            cell_files = os.listdir(cell_path)
            for cell_file in cell_files:
                if cell_file.endswith('.behavioral.v') or \
                ( cell_file.endswith('.v') and cell_file.startswith(library+'__'+cell+'_') ): 
                    cell_file = open(os.path.join(cell_path,cell_file),"r")
                    f.write('\n\n') # separate modules
                    for line in cell_file:
                        # edit these lines
                        if line.startswith('`default_nettype none\n'):
                            line = line.replace('none','wire')
                        # skip these lines
                        if '*' in line: continue  # comments
                        if line.startswith('`include'): continue  # unnecessary imports
                        if ('wire 1' in line): continue  # dunno why this is in some verilog files

                        f.write(line)
        f.close()
    
    def combine_verilog(self,lib_path,library,cells) -> None:
        # set up file
        f = open(os.path.join(self.cache_dir,"verilog",library+".v"), "w")
        #f.write('`define UNIT_DELAY  \n') # WHERE TF IS THIS DEFINED IN PDK?!?!?!
        # include udp models
        models = os.listdir(os.path.join(lib_path,'models'))
        for model in models:
            model_path = os.path.join(self.cache_dir,'verilog','models',library+'__'+model+'.blackbox.v')
            f.write('`include "'+model_path+'"\n')
        # iterate over cells
        for cell in cells:
            cell_path = os.path.join(lib_path,'cells',cell)
            cell_files = os.listdir(cell_path)
            for cell_file in cell_files:
                if cell_file.endswith('.behavioral.v') or \
                (  cell_file.endswith('.v') and cell_file.startswith(library+'__'+cell+'_') ): 
                    cell_file = open(os.path.join(cell_path,cell_file),"r")
                    f.write('\n\n') # separate modules
                    for line in cell_file:
                        # edit these lines
                        if line.startswith('`default_nettype none\n'):
                            line = line.replace('none','wire')
                        # skip these lines
                        if '*' in line: continue  # comments
                        if line.startswith('`include'): continue  # unnecessary imports
                        if ('wire 1' in line): continue  # dunno why this is in some verilog files

                        f.write(line)
        f.close()
    def parse_models(self,lib_path,library) -> None:
        model_path = os.path.join(lib_path,'models')
        models = os.listdir(model_path)
        for model in models:
            cache_model_path = os.path.join(self.cache_dir,'verilog','models')
            model_filename = library+'__'+model+'.blackbox.v'
            f = open(os.path.join(cache_model_path,model_filename),'w')
            model_file = open(os.path.join(model_path,model,model_filename))
            for line in model_file:
                if line.startswith("`default_nettype none"):
                    line = line.replace('none','wire')
                f.write(line)
            f.close()
    def parse_models2(self,lib_path,library) -> None:
        model_path = os.path.join(lib_path,'models')
        models = os.listdir(model_path)
        for model in models:
            cache_model_path = os.path.join(self.cache_dir,'verilog','models')
            model_filename = library+'__'+model+'.v'
            f = open(os.path.join(cache_model_path,model_filename),'w')
            model_file = open(os.path.join(model_path,model,model_filename))
            for line in model_file:
                if line.startswith("`default_nettype none"):
                    line = line.replace('none','wire')
                f.write(line)
            f.close()
    
    def combine_cdl(self,lib_path,library,cells) -> None:
        # set up file
        f = open(os.path.join(self.cache_dir,"cdl",library+".cdl"), "w")
        # iterate over cells
        for cell in cells:
            cell_path = os.path.join(lib_path,'cells',cell)
            cell_files = os.listdir(cell_path)
            for cell_file in cell_files:
                if cell_file.endswith('.cdl'):
                    cell_file = open(os.path.join(cell_path,cell_file),"r")
                    writing=False
                    for line in cell_file:
                        if line.startswith(".SUBCKT"):
                            writing=True
                        if writing:
                            f.write(line)
                        if line.startswith(".ENDS"): 
                            f.write('\n\n')
                            break
        f.close()
    
tech = SkywaterTech()

