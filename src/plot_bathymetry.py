import argparse
from pathlib import Path


import numpy as np
import matplotlib.pyplot as plt
import f90nml
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.colors as mcolors


parser = argparse.ArgumentParser()

parser.add_argument("path")

args = parser.parse_args()

iDir=Path(args.path)

dataFile=f"{iDir}/data"
data_nml = f90nml.read(dataFile)
if not data_nml['parm04']['usingsphericalpolargrid']:
    raise NotImplementedError("plot bathymetry only implemented for sphericalpolargrid")

bathyfile=data_nml['parm05']['bathyfile']
xgorigin=data_nml['parm04']['xgorigin']
ygorigin=data_nml['parm04']['ygorigin']
delx=data_nml['parm04']['delx']
dely=data_nml['parm04']['dely']
nx=len(delx)
ny=len(dely)

lonM = np.zeros(nx)
latM = np.zeros(ny)

lonM[0] = xgorigin + delx[0] * 0.5
latM[0] = ygorigin + dely[0] * 0.5

for i in range(nx-1):
    lonM[i+1] = lonM[i] + (delx[i]+delx[i+1])*0.5

for i in range(ny-1):
    latM[i+1] = latM[i] + (dely[i]+dely[i+1])*0.5

h = np.fromfile(f'{iDir}/{bathyfile}', '>f4').reshape(ny, nx)

ax = plt.axes(projection=ccrs.PlateCarree())
levels = list(np.linspace(-3000,-200,10))[:-1] + list(np.linspace(-200,0,21))
levels = [ -0.0000001 if item == 0.0 else item for item in levels ]

cmap=plt.cm.jet
norm = mcolors.BoundaryNorm(boundaries=levels, ncolors=cmap.N)

cs=ax.contourf(lonM,latM,h,levels=levels, cmap=cmap, norm=norm, transform=ccrs.PlateCarree())
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linestyle='--')
gl.top_labels = False
gl.right_labels = False

plt.colorbar(cs)

plt.savefig('bathymetry.png')
