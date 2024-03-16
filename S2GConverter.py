import os
import sys
import argparse
import subprocess
import math
import shutil
from PIL import Image

MAX_TRIANGLES_CONST = 500
TEXTURE_SIZE_CONST = 256
materialist = {}
model_material_list = {}

WINE_PREFIX = "WINEPREFIX=/home/khang/.local/share/wineprefixes/wine32"
BIN_PATH = "/home/khang/map_compiler/model_tools/S2GConverter"
NO_VTF_PATH = "/home/khang/map_compiler/no_vtf"
MODEL_COMPILE_LOG = "temp.log"

GOLDSRC_MODEL_SUFFIX = "-goldsrc"
OUTPUT_FOLDER = "out"
REPEAT_LOG = "_repeat.log"

def pathcheck(path_to_model):
    resultVar = False
    contains_vtx = False
    contains_vvd = False
    contains_vtf = False
    contains_vmt = False
    if os.path.exists(path_to_model):
        a = os.listdir(os.path.dirname(path_to_model))
        for i in a:
            if '.vtx' in i:
                contains_vtx = True
            if '.vvd' in i:
                contains_vvd = True
            if '.vtf' in i:
                contains_vtf = True
            if '.vmt' in i:
                contains_vmt = True
            if contains_vvd and contains_vtx and contains_vtf and contains_vmt:
                resultVar = True
                break
    print("VTX Detected: "+str(contains_vtx))
    print("VTF Detected: " + str(contains_vtf))
    print("VMT Detected: " + str(contains_vmt))
    print("VVD Detected: " + str(contains_vvd))
    return resultVar

def next_pow_of_two(x):
    a=math.ceil(math.log(x, 2))
    return int(math.pow(2.0, a))

def convert_to_bmp_folder(path_to_vtf):
    # no_vtf doesn't convert to bitmap file
    no_vtf_bin = "no_vtf" if os.name == "posix" else "no_vtf.exe"

    no_vtf_bin = os.path.join(NO_VTF_PATH, no_vtf_bin)
    args = f"{no_vtf_bin} {path_to_vtf} --output-dir {path_to_vtf} --ldr-format png --max-resolution 512 --min-resolution 16"

    os.system(args)

    recursive_convert(path_to_vtf)

def convert_to_bmp(infile):
    if ".png" in infile:
        f, e = os.path.splitext(infile)

        outfile = f + ".bmp"

        if infile != outfile:
            try:
                with Image.open(infile) as im:
                    im = im.quantize(colors=256)
                    im = im.convert(mode='P')
                    im.save(outfile)
            except OSError:
                print("cannot convert", infile)

def recursive_convert(ent):
    if os.path.isfile(ent):
        convert_to_bmp(ent)
        return

    for folders in os.listdir(ent):
        path = os.path.realpath(os.path.join(ent, folders))
        recursive_convert(path)

def decompile_model(path_to_model):
    crowbar_bin = os.path.join(BIN_PATH, "CrowbarCommandLineDecomp.exe")

    args = f"{crowbar_bin} -p {path_to_model}"

    if os.name == "posix":
        args = f"{WINE_PREFIX} wine {args}" 

    os.system(args)
    # subprocess.call(args, shell=True)

def compile_goldsrc_model(path_to_qc):
    # write the output so to know problem about texture
    root = os.path.dirname(path_to_qc)
    studiomdl_bin = os.path.join(root, "studiomdl.exe")

    args = f"{studiomdl_bin} {path_to_qc}"

    if os.name == "posix":
        args = f"wine {args}"

    run_with_log(args)

def run_with_log(args: str):
    command = args.split(" ")
    out = subprocess.run(command, stdout=subprocess.PIPE)

    # long term log
    write_log_path = os.path.join(BIN_PATH, "write.log")

    with open(write_log_path, "a") as f:
        f.write(f"{"-" * 64}\n")
        f.write(args + "\n")
        f.write(out.stdout.decode("utf-8"))
        f.write("\n")

    # # session log
    temp_log_path = os.path.join(BIN_PATH, MODEL_COMPILE_LOG)

    with open(temp_log_path, "w+") as f:
        f.write(out.stdout.decode("utf-8"))
        f.write("\n")

def check_model_compile_log():
    res = False
    model_compile_log = os.path.join(BIN_PATH, MODEL_COMPILE_LOG)

    try:
        with open(model_compile_log, "r+") as f:
            lines = f.readlines()
            lot = len(lines)

            for (index, line) in enumerate(lines):
                if "ERROR" in line:
                    print(f"{"*" * 16} NOT GREAT SUCCESS {"*" * 16}")
                    print(lines[min(index + 1, lot - 1)])
                    print(f"{"*" * 16} Material list {"*" * 16}")
                    print(materialist)

                    res = True
    except IOError:
        pass

    return res

def read_smd_header(path_to_smd):
    header = []
    if path_to_smd.endswith(".smd"):
        with open(path_to_smd) as f:
            filedata = f.readlines()
            for i in filedata:
                if i[:len(i)-1] not in materialist:
                    header.append(i[:len(i)-1])
                else:
                    break
    return fix_header(header[0:len(header)-1])

def fix_header(header):
    for i in range(0, len(header)):
        header[i] = header[i].replace('    ', '')
        header[i] = header[i].replace('  ', '')
    return header

def get_smd_data(path_to_smd):
    truedata = []
    if path_to_smd.endswith(".smd"):
        with open(path_to_smd) as f:
            filedata = f.readlines()
            for i in filedata:
                truedata.append(i[:len(i)-1])
    return truedata

def count_of_polygons(path_to_smd):
    cntr = 0
    if path_to_smd.endswith(".smd"):
        with open(path_to_smd) as f:
            filedata = f.readlines()
            for i in filedata:
                if i[:len(i)-1].lower() in materialist.keys() or i[:len(i)-1].upper() in materialist.keys() or i[:len(i)-1] in materialist.keys() :
                    cntr += 1
    else:
        print("SMD reference reading error! File not found!")
    return cntr

def isnot_texturekey(value, list):
    if value not in list.keys() and value.lower() not in list.keys() and value.upper() not in list.keys():
        return True
    else:
        return False

def read_smd_header(path_to_smd):
    header = []
    if path_to_smd.endswith(".smd") and os.path.exists(path_to_smd):
        with open(path_to_smd) as f:
            filedata = f.readlines()
            if len(materialist)==0:
                print("Error! Materials not found! ")
                return
            for i in filedata:
                if isnot_texturekey(i[:len(i)-1], materialist):
                    header.append(i[:len(i)-1])
                else:
                    break
    return fix_header(header[0:len(header)-1])

# in case the materials are from the sdk
def materiallist_cleanup_FUCK():
    del_list = []
    for (key, value) in materialist.items():
        if len(value) != 0 and value != key:
            materialist[key] = key;
    #     if len(value) == 0:
    #         del_list.append(key)

    # for what in del_list:
    #     del materialist[what]


def split_smd_by_batches(smd_data):
    print('='*100)
    capability = []
    one_verticle_data = []
    materiallist_cleanup_FUCK()

    for i in range(0, len(smd_data)):
        if i%4==0 and i!=0:
            if one_verticle_data[0] in materialist.keys():
                model_material_list[one_verticle_data[0]] = ""

                one_verticle_data[0] = materialist[one_verticle_data[0]]+".bmp"
            elif one_verticle_data[0].lower() in materialist.keys():
                model_material_list[one_verticle_data[0]] = ""

                one_verticle_data[0] = materialist[one_verticle_data[0].lower()] + ".bmp"
            elif  one_verticle_data[0].upper() in materialist.keys():
                model_material_list[one_verticle_data[0]] = ""

                one_verticle_data[0] = materialist[one_verticle_data[0].upper()] + ".bmp"
            else:
                print("Something is realy wrong in materiallist! Are you sure you have all required files?")
                print("Problem material is: ", one_verticle_data[0])

            capability.append(one_verticle_data)
            one_verticle_data = []
        if smd_data[i]!='end':
            one_verticle_data.append(smd_data[i])
    return capability

def polygons_per_part(polygons_amount):
    data = []
    if polygons_amount<=MAX_TRIANGLES_CONST:
        data.append(polygons_amount)
        return data

    while polygons_amount>MAX_TRIANGLES_CONST:
        data.append(MAX_TRIANGLES_CONST)
        polygons_amount-=MAX_TRIANGLES_CONST
    data.append(polygons_amount)
    return data

def find_smd_reference(path_to_model, qc_lines):
    ttf = os.listdir(os.path.dirname(path_to_model))
    smd_reference = []
    # qc_file = ''
    # for i in ttf:
    #     if i.endswith('.qc'):
    #         qc_file = os.path.dirname(path_to_model)+'/'+i
    #         break
    # f = open(qc_file, "r")
    # qc_lines = f.readlines()

    for i in qc_lines:
        j = i.split(' ')
        for s in range(1, len(j)):
            if 'materials' in j[s] or 'anims' in j[s] or 'cd'in i:
                break
            if 'smd' in j[s]:
                j[s] = j[s].replace('\n','').replace('"','')
                smd_reference.append(os.path.join(path_to_model, j[s]))
    for i in smd_reference:
        print("SMD Reference detected: ", i)
    return smd_reference

def get_materials(root):
    basetexture_line = ''
    print("Analyzing .vmt files")
    files = os.listdir(root)

    for i in files:
        if i.endswith('.vmt'):
            curr_file = os.path.join(root, i)
            if not os.path.exists(curr_file):
                print(f"Cannot find {curr_file}. Skip.")
                continue

            vmt_file = open(curr_file, "r")
            lines = vmt_file.readlines()
            for j in lines:
                if 'basetexture' in j.lower():
                    texture_name = ''
                    btx = j.split(' ')
                    for p in range(1, len(btx)):
                        basetexture_line = ''
                        if 'basetexture' in btx[p-1] or 'basetexture' in btx[p-1].lower() or 'basetexture' in btx[p-1].upper():
                            basetexture_line = btx[p]
                            break
                    for k in range(len(basetexture_line)-1, 0, -1):
                        if basetexture_line[k]!='/' and basetexture_line[k]!='/':
                            texture_name = basetexture_line[k]+texture_name
                        else:
                            break
                    texture_name=texture_name[:len(texture_name)-2]
                    materialist[i[:len(i)-4]] = texture_name

        if i.endswith(".bmp"):
            without_bmp_suffix = i[:len(i)-4]
            materialist[without_bmp_suffix] = without_bmp_suffix

    for i in materialist.values():
        print("Detected material: ", i)

# def find_qc(path_to_model):
#     ttf = os.listdir(os.path.dirname(path_to_model))
#     f, e = os.path.splitext(path_to_model)

#     for i in ttf:
#         print(i)
#         if f"{f}.qc" == i:
#             return os.path.realpath(i)

#     return None

def find_animsfolder(path_to_model):
    root = os.path.dirname(path_to_model)
    ttf = os.listdir(root)
    f = os.path.basename(path_to_model).split(".")[0]

    for i in ttf:
        if f'{f}_anims' in i:
            anims_path = os.path.join(root, i)

            return os.path.realpath(anims_path)
    return None

# "unknown studio command: //"
def remove_smd_comment(path_to_smd):
    root = os.path.dirname(path_to_smd)
    ttf = os.listdir(root)
    for i in ttf:
        if ".smd" in i:
            smd_path = os.path.join(root, i)
            with open(smd_path, "r+") as f:
                lines = f.readlines()
                f.seek(0)
                for line in lines:
                    if "//" not in line:
                        f.write(line)
                f.truncate()

def convert_model(path_to_model, parser):
    source_direction = os.getcwd()
    smd_direction = os.path.dirname(path_to_model)

    if pathcheck(path_to_model):
        if not parser.smd_assembly:
            if not parser.no_bmp_convert:
                convert_to_bmp_folder(os.path.dirname(path_to_model))

            decompile_model(path_to_model)

        model_name = os.path.basename(path_to_model).replace(' ', '')
        model_box_data = []

        #grabbing box data
        # qc_file_source = find_qc(path_to_model)
        qc_file_source = os.path.splitext(path_to_model)[0] + ".qc"
        assert qc_file_source != None and os.path.exists(qc_file_source), f"Cannot find .qc file for {path_to_model}"

        qc_file_source_data = open(qc_file_source).readlines()

        for i in qc_file_source_data :
            if "box" in i and not 'hboxset' in i:
                model_box_data.append(i)

        #finding anims folder and moving animations to folder with model files
        anims_folder = find_animsfolder(path_to_model)
        animlist = []
        os.chdir(anims_folder)
        a = os.listdir()

        for p in a:
            anim_file = p.replace(' ', '')
            if anim_file not in animlist:
                animlist.append(anim_file)
                print("Detected animation: ", anim_file)
            try:
                anim_file_path1 = os.path.join(os.getcwd(), p)
                anim_file_path2 = os.path.join(os.getcwd(), anim_file)
                os.rename(anim_file_path1, anim_file_path2)
            except:
                pass
            try:
                anim_file_path = os.path.join(os.getcwd(), anim_file)
                shutil.move(anim_file_path, smd_direction)
            except:
                pass

        os.chdir(smd_direction)

        smd_references = find_smd_reference(os.path.dirname(path_to_model), qc_file_source_data)
        submodels_partnames = []
        submodels_counter = 0
        start_triangle_section = 'triangles'

        for smd_file in smd_references:
            triangle_section_written = False

            # dont write physics
            if "physics" in smd_file:
                continue

            if os.path.exists(smd_file):

                local_partnames = []
                header = read_smd_header(smd_file)
                smd_data = get_smd_data(smd_file)

                if len(smd_data[len(header) + 1:]) > 0:
                    verticle_data = split_smd_by_batches(smd_data[len(header) + 1:])
                else:
                    print("WARNING! SMD data parsing error! It can cause some problems!")
                    print("Excepted: ", smd_file)
                    pass
                parts_amount = math.ceil(len(verticle_data) / MAX_TRIANGLES_CONST)
                if parts_amount==0:
                    parts_amount = 1
                ppt = polygons_per_part(len(verticle_data))
                for part in range(0, parts_amount):
                    print("Writing part: " + str(part + 1))
                    partfile = smd_file[:len(smd_file) - 4] + "_decompiled_part_nr_" + str(part + 1) + "_submodel_" + str(
                        submodels_counter) + ".smd"
                    local_partnames.append(partfile[:len(partfile) - 4])
                    f = open(partfile, "w")
                    if 'triangles' not in header:
                        header.append('triangles')
                    for header_line in header:
                        f.write(header_line)
                        f.write('\n')

                    for verticle in range(0, ppt[part]):
                        writing_data = verticle_data[verticle]
                        for s in range(0, len(writing_data)):
                            writing_data[s] = writing_data[s].replace('  ', '')
                            if s > 0:
                                fixed_data = writing_data[s].split(" ")
                                fixed_data = fixed_data[:9]
                                writing_data[s] = ' '.join(fixed_data)
                        for k in writing_data:
                            f.write(k)
                            f.write('\n')

                    f.write('end\n')
                    f.close()
                    verticle_data = verticle_data[ppt[part]:]
                    print("Part ", str(part + 1), " of sumbodel ", str(submodels_counter), " was successful written")
                    submodels_partnames.append(local_partnames)

        no_mdl_suffix = path_to_model[:len(path_to_model) - 4]

        qc_file = no_mdl_suffix + f"{GOLDSRC_MODEL_SUFFIX}.qc"
        goldsrc_model_name = no_mdl_suffix + f"{GOLDSRC_MODEL_SUFFIX}.mdl"

        f = open(qc_file, "w")
        f.write('$modelname "' + goldsrc_model_name + '"' + '\n')
        f.write('$cd ".\"' + '\n')
        f.write('$cdtexture ".\"' + '\n')
        f.write('$scale 1.0' + '\n')

        if parser.flatshade:
            for key, value in model_material_list.items():
                if len(key) == 0:
                    continue

                # cyberwave
                # if "circuit_board" in key:
                #     f.write(f"$texrendermode \"{key}.bmp\" additive \n")
                # if "chromatic_glass" in key:
                #     f.write(f"$texrendermode \"{key}.bmp\" masked \n")

                f.write(f"$texrendermode \"{key}.bmp\" fullbright \n")
                f.write(f"$texrendermode \"{key}.bmp\" flatshade \n")

        for i in model_box_data:
            # dont write more stupid data
            if "$modelname" in i or "studio \"" in i or ".smd" in i:
                continue

            f.write(i + '\n')
        bodypart_id = 0
        anti_duble = []
        for i in submodels_partnames:
            for j in i:
                if os.path.basename(j) not in anti_duble:
                    f.write('$body "studio' + str(bodypart_id) + '" "' + os.path.basename(j) + '"' + '\n')
                    anti_duble.append(os.path.basename(j))
                    bodypart_id += 1
        for i in animlist:
            f.write('$sequence ' + i[:len(i) - 4] + ' "' + i[:len(i) - 4] + '"' + '\n')
        f.write('\n')
        f.close()

        if os.path.exists(qc_file):
            # shutil.copy(source_direction + '/' + 'studiomdl.exe', os.getcwd())
            remove_smd_comment(path_to_model)
            compile_goldsrc_model(qc_file)

            if check_model_compile_log() and not parser.no_short_circuit:
                sys.exit()

            if parser.move_output:
                move_to_output_folder(goldsrc_model_name)

        print("Great Success!")
    else:
        print("We didn't find all required resources. Are you sure you have .vtf(s), .vmt(s), .vtx, .vvd, .mdl ")

def fix_header(header):
    for i in range(0, len(header)):
        header[i] = header[i].replace('    ', '')
        header[i] = header[i].replace('  ', '')
    return header

def move_to_output_folder(file_path):
    root = os.path.dirname(file_path)
    root = os.path.realpath(root)

    outpath = os.path.join(root, OUTPUT_FOLDER)

    if not os.path.exists(outpath):
        os.makedirs(outpath)

    file_name = os.path.basename(file_path)
    file_name = file_name.replace(GOLDSRC_MODEL_SUFFIX, "")

    outpath_file_name = os.path.join(outpath, file_name)
    os.rename(file_path, outpath_file_name)


def argsparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, help="Path to model you want to convert")
    parser.add_argument('-p', '--path', type=str, help="Path to the folder of model(s) you want to convert")
    parser.add_argument('-E', '--exclude', type=str, help="If model name has this string, exclude from folder conversion.")
    parser.add_argument('-I', '--include', type=str, help="If model name has this string, include in folder conversion (lower priority)")
    parser.add_argument('--test', action='store_true', help="Test input file(s)")
    parser.add_argument("-A", '--smd-assembly', action='store_true', help="Skip everything to work on SMD and QC file")
    parser.add_argument("-C", "--no-bmp-convert", action="store_true", help="Skip BMP conversion step")
    parser.add_argument("-F", "--flatshade", action="store_true", help="Enable flatshade for all textures")
    parser.add_argument("-O", "--move-output", action="store_true", help=f"Move converted models to `{OUTPUT_FOLDER}` folder")
    parser.add_argument("-S", "--no-short-circuit", action="store_true", help="Stop mass conversion as soon as there is error")
    parser.add_argument("-R", "--no-repeat", action="store_true", help=f"Avoid converting model that is converted by checking `{REPEAT_LOG}`. Remember to clean it up.")

    return parser

def print_parser_test(parser):
    print(f"input file {parser.input}")
    print(f"input path {parser.path}")
    print(f"include text `{parser.include}`")
    print(f"exclude text `{parser.exclude}`")
    print(f"smd_assembly {parser.smd_assembly}")
    print(f"no bmp conversion {parser.no_bmp_convert}")
    print(f"flat shade {parser.flatshade}")
    print(f"move output {parser.move_output}")
    print(f"no short circuit {parser.no_short_circuit}")

def main():
    parser = argsparser().parse_args(sys.argv[1:])

    if parser.input and len(parser.input) != 0:
        input_data = format(parser.input)
        assert os.path.isfile(input_data), "The input is not a file"
        assert os.path.exists(input_data), "Model you want to convert doesn't exist"
        input_data = os.path.realpath(input_data)

        if parser.test:
            print_parser_test(parser)
        else:
            root = os.path.dirname(input_data)

            get_materials(root)
            convert_model(input_data, parser)

    elif parser.path and len(parser.path) != 0:
        root = format(parser.path)
        cwd = os.getcwd()

        assert os.path.isdir(root), "The input is not a directory"
        assert os.path.exists(root), "The directory does not exist"

        get_materials(os.path.realpath(root))

        for file in os.listdir(root):
            if ".mdl" not in file:
                continue

            if GOLDSRC_MODEL_SUFFIX in file:
                continue

            if parser.include and len(parser.include):
                include = format(parser.include)
                if include not in file:
                    continue

            if parser.exclude and len(parser.exclude):
                exclude = format(parser.exclude)
                if exclude in file:
                    continue

            # invariants
            os.chdir(cwd)
            # materialist.clear()
            model_material_list.clear()

            # aka .mdl file
            input_data = os.path.realpath(os.path.join(root, file))
            repeat_log_path = os.path.realpath(os.path.join(root, REPEAT_LOG))

            should_skip = False

            if parser.no_repeat:
                try:
                    with open(repeat_log_path, "r") as f:
                        lines = f.readlines()

                        for line in lines:
                            if input_data in line:
                                should_skip = True
                                break
                except IOError:
                    pass

            if parser.test:
                print_parser_test(parser)
                break
            else:
                if should_skip:
                    continue

                convert_model(input_data, parser)

                with open(repeat_log_path, "a+") as f:
                    f.seek(0)
                    f.write(input_data)
                    f.write("\n")

        # sometimes we just don't have the texture
        if not parser.test:
            check_model_compile_log()
            os.remove(os.path.join(BIN_PATH, MODEL_COMPILE_LOG))

if __name__=='__main__':
    main()
