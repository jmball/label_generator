"""Generate a dxf of substrate labels to be laser scribed."""

import calendar
import csv
import ftplib
import getpass
import os
import time

import numpy as np

import ezdxf
import ezdxf.bbox


def main():
    """Run the label generator."""
    # get username
    user = getpass.getuser()

    # set empirical laser etcher x, y offsets
    laser_offset_x = 3.10
    laser_offset_y = 1.92

    # set substrate spacing offset
    offset = 0

    max_substrates = 1

    # set default encapsulation guide
    encapsulation = False

    # prompt user to enter substrate size
    print("\nWelcome to the substrate label generator!\n")
    subw = input("What substrate size are you using? (a=30mm, b=150mm): ")
    if subw == "a":
        subw = 30
        max_substrates = 108

        # update substrate spacing offset
        offset = 1.5

    elif subw == "b":
        subw = 150
    else:
        raise ValueError(f'"{subw}" not recognised. Please enter "a" or "b".')

    # prompt user to enter number of substrates
    substrates = input(
        f"How many substrates are you labelling (max = {max_substrates})?: "
    )
    substrates = int(substrates)
    if substrates > max_substrates:
        raise ValueError(
            f"Number of substrates selected ({substrates}) is greater than maximum "
            + f"allowed ({max_substrates})."
        )

    # prompt user to choose to include encapsulation scratch guide
    encapsulation = input("Do you want encapsulation scratching guides? [y/n]: ")
    if encapsulation == "y":
        encapsulation = True
    elif encapsulation == "n":
        encapsulation = False
    else:
        raise ValueError(f'"{encapsulation}" not recognised. Please enter "y" or "n".')

    # prompt user to choose to include scratch lines
    scratch = input("Do you want common electrode scratching guides? [y/n]: ")
    if scratch == "y":
        scratch = True
    elif scratch == "n":
        scratch = False
    else:
        raise ValueError(f'"{scratch}" not recognised. Please enter "y" or "n".')

    # prompt user to choose to include scratch lines
    scotch = input("Do you want scotch tape guides? [y/n]: ")
    if scotch == "y":
        scotch = True
    elif scotch == "n":
        scotch = False
    else:
        raise ValueError(f'"{scotch}" not recognised. Please enter "y" or "n".')

    # prompt user to choose to include scratch lines
    number = input("Do you want a device 1 mark (+ in corner)? [y/n]: ")
    if number == "y":
        number = True
    elif number == "n":
        number = False
    else:
        raise ValueError(f'"{number}" not recognised. Please enter "y" or "n".')

    # set more substrate parameters
    if subw == 30:
        devices = substrates
        devw = subw
        rows = np.floor((devices - 1) / 8)
    elif subw == 150:
        devices = 25
        devw = 30
        rows = 5 - 1

    print("Please wait a moment while your labels are generated...")

    # set scotchtape width based on 30x30 repeat unit
    scotchw = 20.5

    # set width of guide for common electrode scratching
    comw = 1.5

    # get last used label, username, and timestamp
    label_dir = "substrate_labels"
    with open(f"{label_dir}/substrate_labels.txt", encoding="utf8") as file:
        reader = csv.reader(file, delimiter="\t")
        nums = [row for row in reader]
        last = int(nums[-1][0])

    # create dxf, modelspace, and layers
    dwg = ezdxf.new("R2013")
    msp = dwg.modelspace()
    dwg.layers.new(
        name="lines", dxfattribs={"linetype": "Continuous", "lineweight": 0, "color": 3}
    )
    dwg.layers.new(
        name="border",
        dxfattribs={"linetype": "Continuous", "lineweight": 0, "color": 5},
    )

    # add entities to dxf and get list of labels
    new_labels = []
    for i, num in enumerate(range(last + 1, last + 1 + devices)):
        # create sequential 4-digit hex label
        label = f"{num:06x}".upper()
        timestamp = calendar.timegm(time.gmtime())
        new_labels.append([num, label, user, timestamp])

        # calculate row and col num
        if subw == 30:
            row = np.floor(i / 12)
            col = i % 12
        elif subw == 150:
            row = np.floor(i / 5)
            col = i % 5

        col_offset = offset + 2 * offset * col
        row_offset = offset + 2 * offset * (rows - row)

        # create substrate outline
        points = [
            (col_offset + devw * col, row_offset + (rows - row) * devw),
            (col_offset + devw + devw * col, row_offset + (rows - row) * devw),
            (col_offset + devw + devw * col, row_offset + (rows - row) * devw + devw),
            (col_offset + devw * col, row_offset + (rows - row) * devw + devw),
            (col_offset + devw * col, row_offset + (rows - row) * devw),
        ]
        msp.add_lwpolyline(points, dxfattribs={"layer": "border"})

        # add guides for scratching common electrode area
        if scratch:
            msp.add_line(
                (
                    col_offset + devw * col,
                    row_offset + (rows - row) * devw + (devw / 2) - (comw / 2),
                ),
                (
                    col_offset + devw * col + devw,
                    row_offset + (rows - row) * devw + (devw / 2) - (comw / 2),
                ),
                dxfattribs={"layer": "lines"},
            )
            msp.add_line(
                (
                    col_offset + devw * col,
                    row_offset + (rows - row) * devw + (devw / 2) + (comw / 2),
                ),
                (
                    col_offset + devw * col + devw,
                    row_offset + (rows - row) * devw + (devw / 2) + (comw / 2),
                ),
                dxfattribs={"layer": "lines"},
            )

        # add guides for scotch tape placement
        if scotch:
            msp.add_line(
                (
                    col_offset + devw * col,
                    row_offset + (rows - row) * devw + (devw - scotchw) / 2,
                ),
                (
                    col_offset + devw * col + 2,
                    row_offset + (rows - row) * devw + (devw - scotchw) / 2,
                ),
                dxfattribs={"layer": "lines"},
            )
            msp.add_line(
                (
                    col_offset + devw * col,
                    row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2,
                ),
                (
                    col_offset + devw * col + 2,
                    row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2,
                ),
                dxfattribs={"layer": "lines"},
            )
            msp.add_line(
                (
                    col_offset + devw * col + devw - 2,
                    row_offset + (rows - row) * devw + (devw - scotchw) / 2,
                ),
                (
                    col_offset + devw * col + devw,
                    row_offset + (rows - row) * devw + (devw - scotchw) / 2,
                ),
                dxfattribs={"layer": "lines"},
            )
            msp.add_line(
                (
                    col_offset + devw * col + devw - 2,
                    row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2,
                ),
                (
                    col_offset + devw * col + devw,
                    row_offset + (rows - row) * devw + devw - (devw - scotchw) / 2,
                ),
                dxfattribs={"layer": "lines"},
            )

        # add guides for encapsulation
        if encapsulation is True:
            encapsulation_x_offset = 2.5
            encapsulation_y_offset = 5.75
            encapsulation_points = [
                (
                    col_offset + devw * col + encapsulation_x_offset,
                    row_offset + (rows - row) * devw + encapsulation_y_offset,
                ),
                (
                    col_offset + devw * col + devw - encapsulation_x_offset,
                    row_offset + (rows - row) * devw + encapsulation_y_offset,
                ),
                (
                    col_offset + devw * col + devw - encapsulation_x_offset,
                    row_offset + (rows - row) * devw + devw - encapsulation_y_offset,
                ),
                (
                    col_offset + devw * col + encapsulation_x_offset,
                    row_offset + (rows - row) * devw + devw - encapsulation_y_offset,
                ),
                (
                    col_offset + devw * col + encapsulation_x_offset,
                    row_offset + (rows - row) * devw + encapsulation_y_offset,
                ),
            ]
            msp.add_lwpolyline(encapsulation_points, dxfattribs={"layer": "lines"})

        # add pixel 1 indicator
        if number:
            msp.add_line(
                (col_offset + devw * col + 3, row_offset + (rows - row) * devw + 1),
                (col_offset + devw * col + 3, row_offset + (rows - row) * devw + 3),
                dxfattribs={"layer": "lines"},
            )
            msp.add_line(
                (col_offset + devw * col + 2, row_offset + (rows - row) * devw + 2),
                (col_offset + devw * col + 4, row_offset + (rows - row) * devw + 2),
                dxfattribs={"layer": "lines"},
            )

        # add label
        xpos = col_offset + devw * col + 2
        ypos = row_offset + (rows - row) * devw + devw - 4
        scale = 3

        for j, char in enumerate(label):
            chardwg = ezdxf.readfile(f"reftxt/{char}.dxf")
            charmsp = chardwg.modelspace()
            for k, _ in enumerate(charmsp):
                line = charmsp.query("POLYLINE")[k]
                points = [
                    (xpos + (j + point[0]) * scale, ypos + point[1] * scale)
                    for point in line.points()
                ]
                msp.add_lwpolyline(points, dxfattribs={"layer": "lines"})

    # add a bounding box to account for the empirical offset in the laser etcher
    extents = ezdxf.bbox.extents(msp)

    bounding_points = [
        (extents.extmin[0] - laser_offset_x, extents.extmin[1]),
        (extents.extmin[0] - laser_offset_x, extents.extmax[1] + laser_offset_y),
        (extents.extmax[0], extents.extmax[1] + laser_offset_y),
        (extents.extmax[0], extents.extmin[1]),
        (extents.extmin[0] - laser_offset_x, extents.extmin[1]),
    ]
    msp.add_lwpolyline(bounding_points, dxfattribs={"layer": "border"})

    # save dxf
    dxfname = f"{last + 1:06x}-{last + devices:06x}".upper() + ".dxf"
    dwg.saveas(f"{label_dir}/{dxfname}")

    # add labels to master file
    with open(
        f"{label_dir}/substrate_labels.txt", "a", newline="", encoding="utf8"
    ) as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerows(new_labels)

    # create file for backup
    txtname = dxfname.replace("dxf", "txt")
    backup = f"{label_dir}/{txtname}"
    with open(backup, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerows(new_labels)

    # open ftp connection for server backup
    cerr = False
    werr = False
    try:
        ftp = ftplib.FTP()
        # ftp.set_debuglevel(2)
        ftp.connect("163.1.74.89", 21)
    except Exception:
        cerr = True

    if not cerr:
        ftp.login()

        # create backup dir if needed and make it cwd
        server_dir = "/drop/substrate_labels"
        try:
            ftp.mkd(server_dir)
        except ftplib.error_perm:
            pass
        ftp.cwd(server_dir)

        try:
            # write labels to server
            with open(backup, "rb") as file:
                ftp.storbinary(f"STOR {os.path.basename(backup)}", file)

            # file = open(backup, 'rb')
            # ftp.storbinary(f"STOR {os.path.basename(backup)}", file)
            # file.close()
        except Exception:
            werr = True

        # close ftp connection
        ftp.quit()

    if cerr or werr:
        # log label files that weren't backed up
        errname = "neterr.txt"
        errpath = f"{label_dir}/{errname}"
        with open(errpath, "a", newline="", encoding="utf8") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerows([[dxfname, f"cerr={cerr}", f"werr={werr}"]])

    print("Your labels have been generated!")

    # save newly created file path to a temp file that can be read from a batch file
    with open("temp.txt", "w", encoding="utf8") as file:
        file.write(f"{label_dir}/{dxfname}")

if __name__ == "__main__":
    main()
