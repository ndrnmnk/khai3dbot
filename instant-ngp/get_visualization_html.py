import argparse
import pycolmap
from hloc.utils import viz_3d
import os



def parse_args():
    parser = argparse.ArgumentParser(
        description="Visualize COLMAP model"
    )
    parser.add_argument(
        "--input_dir", required=True, help="path to input folder with model files"
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    # read COLMAP model
    # reconstruction = pycolmap.Reconstruction(f"{args.input_dir}/colmap_text")
    reconstruction = pycolmap.Reconstruction(os.path.join(args.input_dir, "colmap_text"))
    print("#############################################################")
    print(reconstruction.summary())
    print("#############################################################")

    with open(os.path.join(args.input_dir, 'reconstruction_summary.txt'), 'w') as f:
        f.write(reconstruction.summary())

    # create 3d visualization
    fig = viz_3d.init_figure()
    viz_3d.plot_reconstruction(fig, reconstruction, color='rgba(0,255,0,1)', name="mapping", points_rgb=True)
    # fig.show()

    # save visualization to html filw
    fig.write_html(f"{args.input_dir}/sfm_output.html")
    # fig.write_html(os.path.join(args.input_dir, "sfm_output.html"))

if __name__ == "__main__":
    main()
