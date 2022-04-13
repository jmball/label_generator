import calendar
import csv
import ftplib
import getpass
import os
import subprocess
import shutil
import time

import numpy as np

import ezdxf
import ezdxf.bbox

# get username and check whether plotter settings file is 
# in the right folder. Copy it over if needed.
user = getpass.getuser()

# set empirical laser etcher x, y offsets
laser_offset_x = 0.75
laser_offset_y = 0

# set substrate spacing offset
offset = 0

# prompt user to enter substrate size
print('\nWelcome to the substrate label generator!\n')
subw = input('What substrate size are you using? (a=28mm, b=30mm, c=112mm): ')
if subw == 'a':
    subw = 28
elif subw == 'b':
    subw = 30
    holder = input('Are you using the substrate holder? [y/n]: ')
    if holder == 'y':
        # update empirical laser etcher x, y offsets
        laser_offset_x = 2.26
        laser_offset_y = 2.08
        
        # update substrate spacing offset
        offset = 1.5
elif subw == 'c':
    subw = 112
else:
    raise ValueError(
        f'"{subw}" not recognised. Please enter "a", "b", or "c".')

# prompt user to enter number of substrates
substrates = input('How many substrates are you labelling?: ')
substrates = int(substrates)

# prompt user to choose to include scratch lines
scratch = input('Do you want common electrode scratching guides? [y/n]: ')
if scratch == "y":
	scratch = True
elif scratch == "n":
	scratch = False
else:
	raise ValueError(
        f'"{scratch}" not recognised. Please enter "y" or "n".')

# prompt user to choose to include scratch lines
scotch = input('Do you want scotch tape guides? [y/n]: ')
if scotch == "y":
	scotch = True
elif scotch == "n":
	scotch = False
else:
	raise ValueError(
        f'"{scotch}" not recognised. Please enter "y" or "n".')

# prompt user to choose to include scratch lines
number = input('Do you want device number marks (+ and o in corners)? [y/n]: ')
if number == "y":
	number = True
elif number == "n":
	number = False
else:
	raise ValueError(
        f'"{number}" not recognised. Please enter "y" or "n".')

# check if number of substrates is valid
if (subw == 30) or (subw == 28):
    if substrates > 64:
        raise ValueError('The maximum number of 28mm or 30mm substrates is 64')
    devices = substrates
    devw = subw
    rows = np.floor((devices - 1) / 8)
elif subw == 112:
    if substrates != 1:
        raise ValueError('The maximum number of 112mm substrates is 1')
    devices = 16
    devw = 28
    rows = 3

print('Please wait a moment while your labels are generated...')

# determine scotchtape width
if subw == 30:
    scotchw = 20.5
elif (subw == 28) or (subw == 112):
    scotchw = 19

# set width of guide for common electrode scratching
comw = 1.5

# get last used label, username, and timestamp
label_dir = 'substrate_labels'
with open(f'{label_dir}/substrate_labels.txt') as f:
    reader = csv.reader(f, delimiter='\t')
    nums = [row for row in reader]
    last = int(nums[-1][0])

# create dxf, modelspace, and layers
dwg = ezdxf.new('R2013')
msp = dwg.modelspace()
dwg.layers.new(
    name='lines',
    dxfattribs={
        'linetype': 'Continuous',
        'lineweight': 0,
        'color': 3
    })
dwg.layers.new(
    name='border',
    dxfattribs={
        'linetype': 'Continuous',
        'lineweight': 0,
        'color': 5
    })

# add entities to dxf and get list of labels
new_labels = []
for i, num in enumerate(range(last + 1, last + 1 + devices)):
    # create sequential 4-digit hex label
    label = f'{num:06x}'.upper()
    timestamp = calendar.timegm(time.gmtime())
    new_labels.append([num, label, user, timestamp])

    # calculate row and col num
    if (subw == 30) or (subw == 28):
        row = np.floor(i / 8)
        col = i % 8
    elif subw == 112:
        row = np.floor(i / 4)
        col = i % 4

    col_offset = offset + 2 * offset * col
    row_offset = offset + 2 * offset * (rows - row)

    # create substrate outline
    #points = [(devw * col, (rows - row) * devw), (devw + devw * col,
    #                                              (rows - row) * devw),
    #          (devw + devw * col, (rows - row) * devw + devw),
    #          (devw * col, (rows - row) * devw + devw), (devw * col,
    #                                                     (rows - row) * devw)]
    points = [
        (col_offset + devw * col, row_offset + (rows - row) * devw),
        (col_offset + devw + devw * col, row_offset + (rows - row) * devw),
        (col_offset + devw + devw * col, row_offset + (rows - row) * devw + devw),
        (col_offset + devw * col, row_offset + (rows - row) * devw + devw),
        (col_offset + devw * col, row_offset + (rows - row) * devw)
    ]
    msp.add_lwpolyline(points, dxfattribs={'layer': 'border'})

    # add guides for scratching common electrode area
    if scratch:
        #msp.add_line(
        #    (devw * col, (rows - row) * devw + (devw / 2) - (comw / 2)),
        #    (devw * col + devw, (rows - row) * devw + (devw / 2) - (comw / 2)),
        #    dxfattribs={'layer': 'lines'}
        #)
        #msp.add_line(
        #    (devw * col, (rows - row) * devw + (devw / 2) + (comw / 2)),
        #    (devw * col + devw, (rows - row) * devw + (devw / 2) + (comw / 2)),
        #    dxfattribs={'layer': 'lines'}
        #)
        
        msp.add_line(
            (col_offset + devw * col, row_offset + (rows - row) * devw + (devw / 2) - (comw / 2)),
            (col_offset + devw * col + devw, row_offset + (rows - row) * devw + (devw / 2) - (comw / 2)),
            dxfattribs={'layer': 'lines'}
        )
        msp.add_line(
            (col_offset + devw * col, row_offset + (rows - row) * devw + (devw / 2) + (comw / 2)),
            (col_offset + devw * col + devw, row_offset + (rows - row) * devw + (devw / 2) + (comw / 2)),
            dxfattribs={'layer': 'lines'}
        )

    # add guides for scotch tape placement
    if scotch:
        #msp.add_line(
        #    (devw * col, (rows - row) * devw + (devw - scotchw) / 2),
        #    (devw * col + 2, (rows - row) * devw + (devw - scotchw) / 2),
        #    dxfattribs={'layer': 'lines'}
        #)
        #msp.add_line(
        #    (devw * col, (rows - row) * devw + devw - (devw - scotchw) / 2),
        #    (devw * col + 2, (rows - row) * devw + devw - (devw - scotchw) / 2),
        #    dxfattribs={'layer': 'lines'}
        #)
        #msp.add_line(
        #    (devw * col + devw - 2, (rows - row) * devw + (devw - scotchw) / 2),
        #    (devw * col + devw, (rows - row) * devw + (devw - scotchw) / 2),
        #    dxfattribs={'layer': 'lines'}
        #)
        #msp.add_line(
        #    (devw * col + devw - 2,
        #    (rows - row) * devw + devw - (devw - scotchw) / 2),
        #    (devw * col + devw, (rows - row) * devw + devw - (devw - scotchw) / 2),
        #    dxfattribs={'layer': 'lines'}
        #)
        
        msp.add_line(
            (col_offset + devw * col, row_offset + (rows - row) * devw + (devw - scotchw) / 2),
            (col_offset + devw * col + 2, row_offset + (rows - row) * devw + (devw - scotchw) / 2),
            dxfattribs={'layer': 'lines'}
        )
        msp.add_line(
            (col_offset + devw * col, row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2),
            (col_offset + devw * col + 2, row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2),
            dxfattribs={'layer': 'lines'}
        )
        msp.add_line(
            (col_offset + devw * col + devw - 2, row_offset + (rows - row) * devw + (devw - scotchw) / 2),
            (col_offset + devw * col + devw, row_offset + (rows - row) * devw + (devw - scotchw) / 2),
            dxfattribs={'layer': 'lines'}
        )
        msp.add_line(
            (col_offset + devw * col + devw - 2, row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2),
            (col_offset + devw * col + devw, row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2),
            dxfattribs={'layer': 'lines'}
        )

    # add pixel 1 indicator
    if number:
        #msp.add_line(
        #    (devw * col + 3, (rows - row) * devw + 1),
        #    (devw * col + 3,
        #    (rows - row) * devw + 3),
        #    dxfattribs={'layer': 'lines'}
        #)
        #msp.add_line(
        #    (devw * col + 2, (rows - row) * devw + 2),
        #    (devw * col + 4,
        #    (rows - row) * devw + 2),
        #    dxfattribs={'layer': 'lines'}
        #)
        
        msp.add_line(
            (col_offset + devw * col + 3, row_offset + (rows - row) * devw + 1),
            (col_offset + devw * col + 3, row_offset + (rows - row) * devw + 3),
            dxfattribs={'layer': 'lines'}
        )
        msp.add_line(
            (col_offset + devw * col + 2, row_offset + (rows - row) * devw + 2),
            (col_offset + devw * col + 4, row_offset + (rows - row) * devw + 2),
            dxfattribs={'layer': 'lines'}
        )

    # add label
    xpos = col_offset + devw * col + 2
    ypos = row_offset + (rows - row) * devw + devw - 4
    scale = 3

    for i, char in enumerate(label):
        chardwg = ezdxf.readfile(f'reftxt/{char}.dxf')
        charmsp = chardwg.modelspace()
        for j, e in enumerate(charmsp):
            line = charmsp.query('POLYLINE')[j]
            points = [(xpos + (i + point[0]) * scale, ypos + point[1] * scale)
                      for point in line.points()]
            msp.add_lwpolyline(points, dxfattribs={'layer': 'lines'})

# add a bounding box to account for the empirical offset in the laser etcher
extents = ezdxf.bbox.extents(msp)

bounding_points = [
        (extents.extmin[0] - laser_offset_x, extents.extmin[1]),
        (extents.extmin[0] - laser_offset_x, extents.extmax[1] + laser_offset_y),
        (extents.extmax[0], extents.extmax[1] + laser_offset_y),
        (extents.extmax[0], extents.extmin[1]),
        (extents.extmin[0] - laser_offset_x, extents.extmin[1])
    ]
msp.add_lwpolyline(bounding_points, dxfattribs={'layer': 'border'})

# save dxf
dxfname = f'{last + 1:06x}-{last + devices:06x}'.upper() + '.dxf'
dwg.saveas(f'{label_dir}/{dxfname}')

# add labels to master file
with open(f'{label_dir}/substrate_labels.txt', 'a', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(new_labels)

# create file for backup
txtname = dxfname.replace('dxf', 'txt')
backup = f'{label_dir}/{txtname}'
with open(backup, 'w', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerows(new_labels)

# open ftp connection for server backup
cerr = False
werr = False
try:
    ftp = ftplib.FTP()
    # ftp.set_debuglevel(2)
    ftp.connect('163.1.74.89', 21)
except:
    cerr = True

if not cerr:
    ftp.login()

    # create backup dir if needed and make it cwd
    server_dir = '/drop/substrate_labels'
    try:
        ftp.mkd(server_dir)
    except ftplib.error_perm:
        pass
    ftp.cwd(server_dir)

    try:
        # write labels to server
        fp = open(backup, 'rb')
        ftp.storbinary(f'STOR {os.path.basename(backup)}', fp)
        fp.close()

        # # write dxf server
        # fp = open(dxfname, 'rb')
        # ftp.storbinary(f'STOR {os.path.basename(dxfname)}', fp)
        # fp.close()
    except:
        werr = True

    # close ftp connection
    ftp.quit()

if cerr or werr:
    # log label files that weren't backed up
    errname = 'neterr.txt'
    errpath = f'{label_dir}/{errname}'
    with open(errpath, 'a', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows([[dxfname, f'cerr={cerr}', f'werr={werr}']])

print('Your labels have been generated!')
# print('Please wait while the label file opens in AutoCAD...')

# open labels in autocad
# subprocess.run(['C:/Program Files/Autodesk/AutoCAD 2020/acad.exe', f'{label_dir}/{dxfname}'])

# print('Finished!')

# save newly created file path to a temporary file that can be read from a batch file
with open("temp.txt", "w") as f:
    f.write(f'{label_dir}/{dxfname}')
