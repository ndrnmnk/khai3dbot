import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from hlocalization.hloc import extract_features, match_features, reconstruction, pairs_from_sequential
from hlocalization.hloc.utils import viz_3d
from convert_to_splat import convert_to_splat

def get_video_length(filename):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)

def process_splat(user_id, ip):
    ply_path = "temp/res/ply/point_cloud_1000.ply"
    convert_to_splat(ply_path, f"splats/{user_id}.splat")
    try:
        with open("base.html", 'r', encoding='utf-8') as file:
            content = file.read()

        content = content.replace("$UID$", f"{user_id}.splat")
        content = content.replace("$IP$", f"http://{ip}:5000/")

        with open("temp/res.html", 'w', encoding='utf-8') as file:
            file.write(content)

        print("Replacement successful.")
    except Exception as e:
        print(f"Error: {e}")


def restructure_files(input_dir, user_id):
    images_dir = os.path.join(input_dir, "images")
    sfm_dir = os.path.join(input_dir, "sfm")
    html_path = os.path.join(input_dir, "sfm.html")
    sparse_dir = os.path.join("temp", "sparse")
    new_images_dir = os.path.join("temp", "images", "images")

    shutil.rmtree("temp")
    os.mkdir("temp")

    # Ensure the new images directory exists
    if not os.path.exists(new_images_dir):
        os.makedirs(new_images_dir)
        print(f"Created directory: {new_images_dir}")

    # Move images
    for file_name in os.listdir(images_dir):
        file_path = os.path.join(images_dir, file_name)
        if os.path.isfile(file_path):
            shutil.copy(file_path, new_images_dir)
            print(f"Moved {file_name} to {new_images_dir}")

    # Rename 'sfm' to 'sparse' if it exists
    if os.path.exists(sfm_dir):
        os.rename(sfm_dir, sparse_dir)
        print(f"Renamed {sfm_dir} to {sparse_dir}")
    else:
        print(f"'{sfm_dir}' does not exist, skipping rename")

    # Move html
    shutil.move(html_path, f"htmls/{user_id}.html")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare colmap_text filder and HTML file fith sfm visualization"
    )

    parser.add_argument(
        "--dataset_dir", required=True, help="should be separate folder in the root of instant-ngp project, and contain subfolder images"
    )

    parser.add_argument(
        "--output_path", required=True, help="path where to put result html"
    )

    args = parser.parse_args()
    return args

def do_system(arg):
    print(f"==== running: {arg}")
    err = os.system(arg)
    if err:
        print("FATAL: command failed")
        sys.exit(err)

def process_dataset(dataset_dir):
    dataset_name = dataset_dir

    images = Path(dataset_name)
    outputs = Path(dataset_name)

    # if os.path.exists(outputs) and os.path.isdir(outputs):
    # 	shutil.rmtree(outputs)
    # os.mkdir(outputs)

    sfm_pairs = outputs / 'pairs-sfm.txt'
    loc_pairs = outputs / 'pairs-loc.txt'
    sfm_dir = outputs / 'sfm'
    features = outputs / 'features.h5'
    matches = outputs / 'matches.h5'

    # if os.path.exists(outputs) and os.path.isdir(outputs):
    # 	shutil.rmtree(outputs)

    # feature_conf = extract_features.confs['disk']
    # matcher_conf = match_features.confs['disk+lightglue']

    # feature_conf = extract_features.confs['superpoint_aachen']
    # matcher_conf = match_features.confs['superglue']

    # feature_conf = extract_features.confs['superpoint_max']
    # matcher_conf = match_features.confs['superglue']
    #
    # feature_conf = extract_features.confs['superpoint_aachen']
    # matcher_conf = match_features.confs['superglue-fast']

    # feature_conf = extract_features.confs['superpoint_aachen']
    # matcher_conf = match_features.confs['NN-ratio']

    feature_conf = extract_features.confs['superpoint_aachen']
    matcher_conf = match_features.confs['superpoint+lightglue']

    # feature_conf = extract_features.confs['sift']
    # matcher_conf = match_features.confs['sift+lightglue']

    # feature_conf = extract_features.confs['sift']
    # feature_conf = extract_features.confs['rootsift']
    # matcher_conf = match_features.confs['NN-mutual-dist_0.7']
    # matcher_conf = match_features.confs['NN-mutual']

    # feature_conf = extract_features.confs['superpoint_aachen']
    # matcher_conf = match_features.confs['NN-mutual']

    # feature_conf = extract_features.confs['aliked']
    # # matcher_conf = match_features.confs['NN-mutual-dist_0.7']
    # todo not ready yet
    # matcher_conf = match_features.confs['superglue']

    # todo not ready yet
    # feature_conf = extract_features.confs['keynet']
    # matcher_conf = match_features.confs['NN-ratio']


    # First we list the images used for mapping
    references = [p.relative_to(images).as_posix() for p in (images / 'images/').iterdir()]
    print(len(references), "mapping images")
    # plot_images([read_image(images / r) for r in references], dpi=25)
    # plt.show()

    # Then we extract features and match them across image pairs.
    # Since we deal with few images, we simply match all pairs exhaustively.
    # For larger scenes, we would use image retrieval.
    extract_features.main(feature_conf, images, image_list=references, feature_path=features)
    # pairs_from_exhaustive.main(sfm_pairs, image_list=references)
    pairs_from_sequential.main(sfm_pairs, image_list=references)
    match_features.main(matcher_conf, sfm_pairs, features=features, matches=matches)

    # Then we run incremental Structure-From-Motion and display the reconstructed 3D model.
    model = reconstruction.main(sfm_dir, images, sfm_pairs, features, matches, image_list=references)

    print(model.summary())


    # fig = viz_3d.init_figure(template="plotly_dark")
    fig = viz_3d.init_figure()
    viz_3d.plot_reconstruction(fig, model, color='rgba(0,255,0,1)', name="mapping", points_rgb=True)

    # write html
    fig.write_html(f"{outputs}/sfm.html")


def process_vid(user_id):
    video_path = f"videos/{user_id}"
    frame_count = 30
    fps = int(frame_count / get_video_length(f"{video_path}/input_video.mp4"))

    if os.path.exists(f"{video_path}/images"):
        shutil.rmtree(f"{video_path}/images")
        shutil.rmtree(f"{video_path}/sfm")
    os.makedirs(f"{video_path}/images")
    os.makedirs(f"{video_path}/sfm")

    cut_process = subprocess.Popen(["ffmpeg", "-i", f"{video_path}/input_video.mp4", "-vf", f"fps={fps}", f"{video_path}/images/%04d.jpg"])
    cut_process.wait()

    process_dataset(video_path)
    restructure_files(video_path, str(user_id))