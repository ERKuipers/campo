import math
import os
import subprocess
import tempfile
import shutil

from osgeo import gdal, osr
import pandas as pd

from ..dataframe import *
from ..utils import _color_message

gdal.UseExceptions()


def to_df(dataframe, timestep=None):
    """ Exports point agent properties to a Pandas dataframe

    :param dataframe: Input dataframe from LUE dataset
    :type dataframe: dataframe
    :param crs: Coordinate Reference System, e.g. 'EPSG:4326'
    :type crs: str
    :param timestep: None for static data or timestep for dynamic data
    :type timestep: int
    """

    phen_name = dataframe.keys()

    if not timestep:

        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]

                if propset['_campo_space_type'] == 'static_same_point':
                    dfObj = pd.DataFrame()

                    property_names = list(propset.keys())
                    property_names.remove('_campo_space_type')

                    for prop_name in property_names:
                        dfObj['CoordX'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                        dfObj['CoordY'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

                        for prop_name in property_names:
                            prop = dataframe[phen_name][pset_name][prop_name]
                            dfObj[prop_name] = prop['values'].data

                    return dfObj
                else:
                    msg = _color_message('Only for static point agents')
                    raise TypeError(msg)

    else:

        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]

                if not propset['_campo_space_type'] == 'dynamic_same_point':
                    raise NotImplementedError

                dfObj = pd.DataFrame()

                property_names = list(propset.keys())
                property_names.remove('_campo_space_type')

                for prop_name in property_names:
                    dfObj['CoordX'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                    dfObj['CoordY'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

                for prop_name in property_names:
                    p = dataframe[phen_name][pset_name][prop_name]
                    # User provided timestep to array index
                    ts = timestep - 1
                    dfObj[prop_name] = p['values'].values[:, ts]

                    return dfObj


def mobile_points_to_gpkg(coords, dataframe, filename, crs=""):

    # rewrite coordinates with ones from current timestep
    dataframe["CoordX"] = coords[:, 0]
    dataframe["CoordY"] = coords[:, 1]

    with tempfile.TemporaryDirectory() as tmpdir:
        layername, tail = os.path.splitext(os.path.basename(filename))

        csv_fname = os.path.join(tmpdir, f'{layername}.csv')
        csvt_fname = os.path.join(tmpdir, f'{layername}.csvt')

        columns = []
        for c in dataframe:
            if dataframe[c].dtype.kind == 'f':
                columns.append('Real')
            elif dataframe[c].dtype.kind == 'i':
                columns.append('Integer')
            else:
                columns.append('String')

        columns = ','.join(map(str, columns))
        with open(csvt_fname, 'w') as content:
            content.write(columns)

        dataframe.to_csv(csv_fname, index=False)

        s_srs = ''
        t_srs = ''
        if crs != '':
            s_srs = f'-s_srs {crs}'
            t_srs = f'-t_srs {crs}'

        cmd = f'ogr2ogr {s_srs} {t_srs} -oo X_POSSIBLE_NAMES=CoordX -oo Y_POSSIBLE_NAMES=CoordY -f GPKG {filename} {csv_fname}'
        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)


def to_gpkg(dataframe, filename, crs='', timestep=None):
    """ Exports point agent properties to a GeoPackage

    :param dataframe: Input dataframe from LUE dataset
    :type dataframe: dataframe
    :param filename: Output filename
    :type filename: str
    :param crs: Coordinate Reference System, e.g. 'EPSG:4326'
    :type crs: str
    :param timestep: None for static data or timestep for dynamic data
    :type timestep: int
    """

    phen_name = dataframe.keys()

    if not timestep:

        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]

                if propset['_campo_space_type'] == 'static_same_point':
                    dfObj = pd.DataFrame()

                    property_names = list(propset.keys())
                    property_names.remove('_campo_space_type')

                    for prop_name in property_names:
                        dfObj['CoordX'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                        dfObj['CoordY'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

                        for prop_name in property_names:
                            prop = dataframe[phen_name][pset_name][prop_name]
                            dfObj[prop_name] = prop['values'].data

                    with tempfile.TemporaryDirectory() as tmpdir:
                        layername, tail = os.path.splitext(os.path.basename(filename))

                        csv_fname = os.path.join(tmpdir, f'{layername}.csv')
                        csvt_fname = os.path.join(tmpdir, f'{layername}.csvt')

                        columns = []
                        for c in dfObj:
                            if dfObj[c].dtype.kind == 'f':
                                columns.append('Real')
                            elif dfObj[c].dtype.kind == 'i':
                                columns.append('Integer')
                            else:
                                columns.append('String')

                        columns = ','.join(map(str, columns))
                        with open(csvt_fname, 'w') as content:
                            content.write(columns)

                        dfObj.to_csv(csv_fname, index=False)

                        s_srs = ''
                        t_srs = ''
                        if crs != '':
                            s_srs = f'-s_srs {crs}'
                            t_srs = f'-t_srs {crs}'

                        cmd = f'ogr2ogr {s_srs} {t_srs} -oo X_POSSIBLE_NAMES=CoordX -oo Y_POSSIBLE_NAMES=CoordY -f GPKG {filename} {csv_fname}'
                        subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)

                #elif propset['_campo_space_type'] == 'static_same_field':
                    #raise NotImplementedError
                #elif propset['_campo_space_type'] == 'static_diff_field':
                    #raise NotImplementedError
                else:
                    msg = _color_message('Only for static point agents')
                    raise TypeError(msg)

    else:

        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]

                if not propset['_campo_space_type'] == 'dynamic_same_point':
                    raise NotImplementedError

                dfObj = pd.DataFrame()

                property_names = list(propset.keys())
                property_names.remove('_campo_space_type')

                for prop_name in property_names:
                    dfObj['CoordX'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                    dfObj['CoordY'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

                for prop_name in property_names:
                    p = dataframe[phen_name][pset_name][prop_name]
                    # User provided timestep to array index
                    ts = timestep - 1
                    dfObj[prop_name] = p['values'].values[:, ts]

                with tempfile.TemporaryDirectory() as tmpdir:
                    layername, tail = os.path.splitext(os.path.basename(filename))

                    csv_fname = os.path.join(tmpdir, f'{layername}{timestep}.csv')
                    csvt_fname = os.path.join(tmpdir, f'{layername}{timestep}.csvt')

                    columns = []
                    for c in dfObj:
                        if dfObj[c].dtype.kind == 'f':
                            columns.append('Real')
                        elif dfObj[c].dtype.kind == 'i':
                            columns.append('Integer')
                        else:
                            columns.append('String')

                    columns = ','.join(map(str, columns))
                    with open(csvt_fname, 'w') as content:
                        content.write(columns)

                    dfObj.to_csv(csv_fname, index=False)

                    s_srs = ''
                    t_srs = ''
                    if crs != '':
                        s_srs = f'-s_srs {crs}'
                        t_srs = f'-t_srs {crs}'

                    ofilename = f'{layername}_{timestep}.gpkg'
                    cmd = f'ogr2ogr {s_srs} {t_srs} -oo X_POSSIBLE_NAMES=CoordX -oo Y_POSSIBLE_NAMES=CoordY -f GPKG {ofilename} {csv_fname}'
                    subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)


def to_tiff(dataframe, crs="", directory="", timestep=None):
    """ Exports field agent property to a set of GeoTIFF outputs

    :param dataframe: Input dataframe from LUE dataset
    :type dataframe: dataframe
    :param crs: Coordinate Reference System, e.g. 'EPSG:4326'
    :type crs: str
    :param directory: Output directory
    :type directory: str
    :param timestep: None for static data or timestep for dynamic data
    :type timestep: int
    """

    if not timestep:
        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]
                if propset['_campo_space_type'] == 'static_same_point': # or propset['_campo_space_type'] == 'diff_same_point':
                    msg = _color_message('Only for field agents')
                    raise TypeError(msg)

                property_names = list(propset.keys())
                property_names.remove('_campo_space_type')

                for prop_name in property_names:
                    objects = dataframe[phen_name][pset_name][prop_name]

                    for obj_id in objects:
                        obj = objects[obj_id]

                        rows = obj.values.shape[0]
                        cols = obj.values.shape[1]
                        cellsize = math.fabs(obj.xcoord[1].values - obj.xcoord[0].values)

                        data = obj.data
                        xmin = obj.xcoord[0].values.item()
                        # last ycoordinate is the lower of the topmost row, we need the upper ycoordinate for the extent
                        ymax = obj.ycoord[-1].values.item() + cellsize
                        geotransform = (xmin, cellsize, 0, ymax, 0, -cellsize)

                        out_id = int(obj_id + 1)
                        fname = os.path.join(directory, f'{prop_name}_{out_id}.tiff')

                        dtype = None
                        if data.dtype.kind == 'f':
                            dtype = gdal.GDT_Float32
                        elif data.dtype.kind == 'i':
                            dtype = gdal.GDT_Int32
                        elif data.dtype.kind == 'u':
                            dtype = gdal.GDT_Byte
                        else:
                            raise NotImplementedError

                        dst_ds = gdal.GetDriverByName('GTiff').Create(fname, cols, rows, 1, dtype)
                        dst_ds.SetGeoTransform(geotransform)

                        if crs != '':
                            aut, code = crs.split(':')
                            if aut != 'EPSG':
                                msg = _color_message('Provide CRS as EPSG code, e.g."EPSG:4326"')
                                raise TypeError(msg)

                            srs = osr.SpatialReference()
                            srs.ImportFromEPSG(int(code))
                            dst_ds.SetProjection(srs.ExportToWkt())

                        dst_ds.GetRasterBand(1).WriteArray(data)
                        dst_ds = None
    else:
        for phen_name in dataframe.keys():
            phen = dataframe[phen_name]
            for pset_name in phen.keys():
                propset = dataframe[phen_name][pset_name]
                assert propset['_campo_space_type'] == dynamic_diff_field
                if not (propset['_campo_space_type'] == 'dynamic_same_field' or propset['_campo_space_type'] == 'dynamic_diff_field'):
                    msg = _color_message('Only for field agents')
                    raise TypeError(msg)

                raise NotImplementedError


def to_csv(dataframe, filename):
    """ Exports point agent properties to a CSV

    :param dataframe: Input dataframe from LUE dataset
    :type dataframe: dataframe
    :param filename: Output filename
    :type filename: str
    """

    fname, tail = os.path.splitext(os.path.basename(filename))
    phen_name = dataframe.keys()

    dfObj = pd.DataFrame()

    for phen_name in dataframe.keys():
        phen = dataframe[phen_name]
        for pset_name in phen.keys():
            propset = dataframe[phen_name][pset_name]

            if propset['_campo_space_type'] == 'dynamic_same_point':

                property_names = list(propset.keys())
                property_names.remove('_campo_space_type')

                for prop_name in property_names:
                    xcoord = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                    ycoord = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]
                    dfObj = pd.DataFrame()
                    dfObj['CoordX'] = xcoord
                    dfObj['CoordY'] = ycoord
                    coordname = f'{fname}_coords.csv'
                    dfObj.to_csv(coordname, index=False)

                    dfObj = pd.DataFrame()
                    p = dataframe[phen_name][pset_name][prop_name]
                    obj_values = p['values']
                    for a in range(p['values'].shape[0]):
                        dfObj[f'ag{a}'] = p['values'].values[a]

                    outname = f'{fname}_{prop_name}.csv'
                    dfObj.to_csv(outname, index=False)

            elif propset['_campo_space_type'] == 'static_same_point':
                dfObj = pd.DataFrame()

                property_names = list(propset.keys())
                property_names.remove('_campo_space_type')

                for prop_name in property_names:
                    dfObj['CoordX'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                    dfObj['CoordY'] = dataframe[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

                for prop_name in property_names:
                    prop = dataframe[phen_name][pset_name][prop_name]
                    dfObj[prop_name] = prop['values'].data

                outname = f'{fname}.csv'
                dfObj.to_csv(outname, index=False)

            else:
                raise NotImplementedError

    return

            #for prop_name in propset.keys():
                #dfObj['CoordX'] = frame[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                #dfObj['CoordY'] = frame[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

            #for prop_name in propset.keys():
                #prop = frame[phen_name][pset_name][prop_name]

                #dfObj[prop_name] = prop['values'].data

    ##fname, tail = os.path.splitext(os.path.basename(filename))

    ##csv_fname = f'{fname}.csv'

    #dfObj.to_csv(filename, index=False)


def create_point_pdf(frame, filename):

    phen_name = frame.keys()

    wdir = os.getcwd()
    data_dir = os.path.join(wdir, 'data')

    tmp_csv = os.path.join(data_dir, 'agents.csv')

    phen_name = frame.keys()

    dfObj = pd.DataFrame()

    for phen_name in frame.keys():
        phen = frame[phen_name]
        for pset_name in phen.keys():
            propset = frame[phen_name][pset_name]

            for prop_name in propset.keys():
                dfObj['x'] = frame[phen_name][pset_name][prop_name]['coordinates'].data[:, 0]
                dfObj['y'] = frame[phen_name][pset_name][prop_name]['coordinates'].data[:, 1]

            for prop_name in propset.keys():
                prop = frame[phen_name][pset_name][prop_name]

                dfObj[prop_name] = prop['values'].data

    dfObj.to_csv(tmp_csv, index=False)

    gpkg_fname_out = os.path.join(data_dir, 'agents.gpkg')

    cmd = 'ogr2ogr -s_srs EPSG:28992 -t_srs EPSG:28992 -oo X_POSSIBLE_NAMES=x -oo Y_POSSIBLE_NAMES=y -f GPKG {} {}'.format(gpkg_fname_out, tmp_csv)

    subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)

    cmd = 'gdal_translate -of PDF -a_srs EPSG:28992 data/clone.tiff points.pdf -co OGR_DATASOURCE=out.vrt'

    clone_path = os.path.join(data_dir, 'clone.tiff')
    vrt_path = os.path.join(data_dir, 'sources.vrt')
    cmd = 'gdal_translate -of PDF -a_srs EPSG:28992 {} {} -co OGR_DATASOURCE={}'.format(clone_path, filename, vrt_path)

    subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)


def create_field_pdf(frame, filename):

    phen_name = frame.keys()

    wdir = os.getcwd()
    data_dir = os.path.join(wdir, 'data')

    tmpdir = 'tmp'
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)

    os.mkdir(tmpdir)

    #with tempfile.TemporaryDirectory() as tmpdir:
    fnames = []
    lnames = []

    for phen_name in frame.keys():
        phen = frame[phen_name]
        for pset_name in phen.keys():
            propset = frame[phen_name][pset_name]

            for prop_name in propset.keys():

                objects = frame[phen_name][pset_name][prop_name]

                for obj_id in objects:
                    obj = objects[obj_id]

                    rows = obj.values.shape[0]
                    cols = obj.values.shape[1]
                    cellsize = math.fabs(obj.xcoord[1].values - obj.xcoord[0].values)

                    data = obj.data
                    data = data/(data.max()/250.0)
                    xmin = obj.xcoord[0].values.item()
                    ymax = obj.ycoord[-1].values.item()
                    geotransform = (xmin, cellsize, 0, ymax, 0, -cellsize)

                    fname = os.path.join(tmpdir, '{:03d}'.format(obj_id))
                    #fname = os.path.join('{:03d}'.format(obj_id))
                    fnames.append(fname)
                    lnames.append('shop{:03d}'.format(obj_id))

                    dst_ds = gdal.GetDriverByName('GTiff').Create(fname, cols, rows, 1, gdal.GDT_Byte)
                    dst_ds.SetGeoTransform(geotransform)
                    srs = osr.SpatialReference()
                    srs.ImportFromEPSG(28992)
                    dst_ds.SetProjection(srs.ExportToWkt())
                    dst_ds.GetRasterBand(1).WriteArray(data)
                    dst_ds = None

    outfile = os.path.join(wdir, filename)
    clone = os.path.join(data_dir, 'clone.tiff')
    roads = os.path.join(data_dir, 'roads.gpkg')
    roads = os.path.join(data_dir, 'sources.vrt')

    rasters = ','.join(fnames)
    names = ','.join(lnames)

    cmd = 'gdal_translate -q -of PDF -a_srs EPSG:28992 {} {} -co OGR_DATASOURCE={} -co OGR_DISPLAY_FIELD="roads" -co EXTRA_RASTERS={} -co EXTRA_RASTERS_LAYER_NAME={} -co OFF_LAYERS={}'.format(clone, outfile, roads, rasters, names, names )
    #cmd = 'gdal_translate -q -of PDF -a_srs EPSG:28992 {} {} -co OGR_DATASOURCE={} -co OGR_DISPLAY_FIELD="roads" -co EXTRA_RASTERS={} -co EXTRA_RASTERS_LAYER_NAME={}'.format(clone, outfile,roads,rasters,names)
    cmd = 'gdal_translate -q -of PDF -a_srs EPSG:28992 {} {} -co OGR_DATASOURCE={} -co EXTRA_RASTERS={} -co EXTRA_RASTERS_LAYER_NAME={}'.format(clone, outfile, roads, rasters, names)

    subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL)
    shutil.rmtree(tmpdir)


def _gdal_datatype(data_type):
    """ return corresponding GDAL datatype """

    if data_type == 'bool':
        return gdal.GDT_Byte
    elif data_type == 'int32':
        return gdal.GDT_Int32
    elif data_type == 'int64':
        return gdal.GDT_Int64
    elif data_type == 'float32':
        return gdal.GDT_Float32
    elif data_type == 'float64':
        return gdal.GDT_Float64
    else:
        raise ValueError(f"Data type '{data_type}' non-suported")


def to_geotiff(dataframe, path: str, crs: str) -> None:
    """ Exports field agent property to a GeoTIFF

    :param dataframe: Input dataframe from LUE dataset for particular timestep
    :param path: Output path
    :param crs: Coordinate Reference System, e.g. "EPSG:4326"
    """

    if crs != "":
        aut, code = crs.split(":")
        if aut != "EPSG":
            msg = _color_message('Provide CRS like "EPSG:4326"')
            raise TypeError(msg)

    rows = dataframe.values.shape[0]
    cols = dataframe.values.shape[1]
    cellsize_x = math.fabs(dataframe.xcoord[1].values - dataframe.xcoord[0].values)
    cellsize_y = math.fabs(dataframe.ycoord[1].values - dataframe.ycoord[0].values)

    data = dataframe.data

    xmin = dataframe.xcoord[0].values.item()
    # last ycoordinate is the lower of the topmost row, we need the upper ycoordinate for the extent
    ymax = dataframe.ycoord[-1].values.item() + cellsize_y
    geotransform = (xmin, cellsize_x, 0, ymax, 0, -cellsize_y)

    out_ds = gdal.GetDriverByName('GTiff').Create(str(path), cols, rows, 1, _gdal_datatype(data.dtype))
    out_ds.SetGeoTransform(geotransform)

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(int(code))
    out_ds.SetProjection(srs.ExportToWkt())

    out_ds.GetRasterBand(1).WriteArray(data)
    out_ds = None
