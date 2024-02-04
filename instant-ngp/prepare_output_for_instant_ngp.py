import tqdm
from matplotlib import pyplot as plt
from pathlib import Path
import numpy as np
import os
import sys
import shutil
from hloc import extract_features, match_features, reconstruction, pairs_from_exhaustive
from hloc.instant_ngp_utils import get_transforms_from_sfm_text_output
from hloc.visualization import plot_images, read_image
from hloc.utils import viz_3d
import pycolmap
from hloc.localize_sfm import QueryLocalizer, pose_from_cluster
import argparse


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


	# feature_conf = extract_features.confs['superpoint_aachen']
	# matcher_conf = match_features.confs['superpoint+lightglue']

	feature_conf = extract_features.confs['sift']
	# matcher_conf = match_features.confs['sift+lightglue']

	# feature_conf = extract_features.confs['sift']
	# feature_conf = extract_features.confs['rootsift']
	matcher_conf = match_features.confs['NN-mutual-dist_0.7']
	# matcher_conf = match_features.confs['NN-mutual']

	# feature_conf = extract_features.confs['superpoint_aachen']
	# matcher_conf = match_features.confs['NN-mutual-dist_0.7']
	#

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
	pairs_from_exhaustive.main(sfm_pairs, image_list=references)
	match_features.main(matcher_conf, sfm_pairs, features=features, matches=matches)

	# Then we run incremental Structure-From-Motion and display the reconstructed 3D model.
	model = reconstruction.main(sfm_dir, images, sfm_pairs, features, matches, image_list=references)

	print(model.summary())


	# fig = viz_3d.init_figure(template="plotly_dark")
	fig = viz_3d.init_figure()
	viz_3d.plot_reconstruction(fig, model, color='rgba(0,255,0,1)', name="mapping", points_rgb=True)

	if os.path.exists(f"{outputs}/../../django3d/viewer/templates/viewer/sfm/{args.output_path}"):
		shutil.rmtree(f"{outputs}/../../django3d/viewer/templates/viewer/sfm/{args.output_path}")
	os.mkdir(f"{outputs}/../../django3d/viewer/templates/viewer/sfm/{args.output_path}")

	# fig.show()
	fig.write_html(f"{outputs}/../../django3d/viewer/templates/viewer/sfm/{args.output_path}/sfm_output.html")

	# # create subdir for instant ngp
	# ingp_outputs = f"{outputs}/for_ingp/"
	# if os.path.exists(ingp_outputs) and os.path.isdir(ingp_outputs):
	# 	shutil.rmtree(ingp_outputs)
	# os.mkdir(ingp_outputs)
	#
	#
	# # save colmap_sparse
	# sparse_output_path = f"{ingp_outputs}/colmap_sparse/"
	# os.mkdir(sparse_output_path)
	#
	# do_system(f"colmap mapper --database_path {os.path.join(sfm_dir, 'database.db')} --image_path {images} --output_path {sparse_output_path}")
	# do_system(
	# 	f"colmap bundle_adjuster --input_path {sparse_output_path}/0 --output_path {sparse_output_path}/0 --BundleAdjustment.refine_principal_point 1")
	#
	# # save colmap_text
	# text_output_path = f"{ingp_outputs}/colmap_text/"
	# os.mkdir(text_output_path)
	# model.write_text(text_output_path)
	#
	#
	# get_transforms_from_sfm_text_output(text_output_path, images, os.path.join(ingp_outputs, "transforms.json"))

	# ingp_images = os.path.join(ingp_outputs, "images")
	# os.mkdir(ingp_images)
	# do_system(f"cp -r {os.path.join(images, 'mapping/')}. {ingp_images}")

if __name__ == "__main__":
	main()
