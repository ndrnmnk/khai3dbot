from pathlib import Path
import os
import sys
import shutil
from hloc import extract_features, match_features, reconstruction, pairs_from_sequential
from hloc.utils import viz_3d
import argparse


def restructure_files(input_dir, output_dir):
    images_dir = os.path.join(input_dir, "images")
    sfm_dir = os.path.join(input_dir, "sfm")
    sparse_dir = os.path.join(output_dir, "sparse")
    new_images_dir = os.path.join(output_dir, "images", "images")

    # Ensure the new images directory exists
    if not os.path.exists(new_images_dir):
        os.makedirs(new_images_dir)
        print(f"Created directory: {new_images_dir}")

    # Move all files from images/ to images/images/
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

def main():
	args = parse_args()

	dataset_name = args.dataset_dir

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

	if os.path.exists(f"{outputs}/../../htmls/{args.output_path}"):
		shutil.rmtree(f"{outputs}/../../htmls/{args.output_path}")
	os.makedirs(f"{outputs}/../../htmls/{args.output_path}", exist_ok=True)

	# write html
	fig.write_html(f"{outputs}/../../htmls/{args.output_path}/sfm_output.html")

	restructure_files(outputs, f"{outputs}/../../htmls/")


if __name__ == "__main__":
	main()