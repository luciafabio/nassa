import pathlib
import itertools

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.colors import ListedColormap


def get_axes(subunit_len, base):
    # define list for axes ticks to inforce label order,
    # so its the same as the paper
    yaxis = [
        f"{base}{base}",
        f"{base}C",
        f"C{base}",
        "CC",
        f"G{base}",
        "GC",
        f"A{base}",
        "AC",
        f"{base}G",
        f"{base}A",
        "CG",
        "CA",
        "GG",
        "GA",
        "AG",
        "AA"]
    if subunit_len == 4:
        xaxis = yaxis[::-1]
    elif subunit_len == 3:
        xaxis = f"G A C {base}".split()

    # Tetra order starts with last flank and first basepair,
    # iterates over basepairs first, and then over flanks.
    # This is because the plot is populated from bottom left to top right
    tetramer_order = [b.join(f) for f in yaxis for b in xaxis]
    return xaxis, yaxis, tetramer_order


def reorder_labels(df, subunit_name, tetramer_order):
    # sort values according to tetramer order in axes
    sorted_index = dict(zip(tetramer_order, range(len(tetramer_order))))
    df["subunit_rank"] = df[subunit_name].map(sorted_index)
    df = df.sort_values(by="subunit_rank")
    df = df.drop("subunit_rank", axis=1)
    df = df.reset_index(drop=True)
    return df


def arlequin_plot(
        df,
        global_mean,
        global_std,
        helpar,
        save_path,
        unit_name="tetramer",
        unit_len=4,
        base="T",
        label_offset=0.5):

    xaxis, yaxis, tetramer_order = get_axes(unit_len, base)
    df = reorder_labels(df, unit_name, tetramer_order)

    # axis labels
    sep = "." * (unit_len - 2)
    yaxis_labels = [sep.join(f) for f in yaxis]

    # data to plot
    sz1 = df["col1"].ravel()
    sz2 = df["col2"].ravel()

    # build triangle arrays for plot
    # N: flanks combinations
    # M: subunit middle-part combinations
    N = 4 ** 2
    M = 4 ** (unit_len - 2)
    x = np.arange(M + 1)
    y = np.arange(N + 1)
    xs, ys = np.meshgrid(x, y)
    upper_triangle = [(i + j*(M+1), i+1 + j*(M+1), i+1 + (j+1)*(M+1))
                      for j in range(N) for i in range(M)]
    lower_triangle = [(i + j*(M+1), i+1 + (j+1)*(M+1), i + (j+1)*(M+1))
                      for j in range(N) for i in range(M)]
    triang1 = Triangulation(xs.ravel(), ys.ravel(), upper_triangle)
    triang2 = Triangulation(xs.ravel(), ys.ravel(), lower_triangle)

    # build plots
    fig, axs = plt.subplots(
        1,
        1,
        dpi=300,
        tight_layout=True)

    colormap = plt.get_cmap("bwr", 3).reversed()
    colormap.set_bad(color="grey")
    img1 = axs.tripcolor(triang1, sz1, cmap=colormap, vmin=-1, vmax=1)
    _ = axs.tripcolor(triang2, sz2, cmap=colormap, vmin=-1, vmax=1)

    axs.grid()
    xlocs = np.arange(len(xaxis))
    ylocs = np.arange(len(yaxis))
    _ = axs.set_xticks(xlocs)
    _ = axs.set_xticklabels("")
    _ = axs.set_yticks(ylocs)
    _ = axs.set_yticklabels("")
    _ = axs.set_xticks(xlocs+label_offset, minor=True)
    _ = axs.set_xticklabels(xaxis, minor=True)
    _ = axs.set_yticks(ylocs+label_offset, minor=True)
    _ = axs.set_yticklabels(yaxis_labels, minor=True)

    _ = axs.set_xlim(0, M)
    _ = axs.set_ylim(0, N)
    axs.set_title(helpar.upper())
    cbar = fig.colorbar(img1, ax=axs, ticks=[-1, 0, 1])
    cbar.ax.set_yticklabels([
        f"< {global_mean:.2f}-{global_std:.2f}",
        f"{global_mean:.2f}$\pm${global_std:.2f}",
        f"> {global_mean:.2f}+{global_std:.2f}"])

    file_path = pathlib.Path(save_path) / f"{helpar}.pdf"
    fig.savefig(fname=file_path, format="pdf")
    return fig, axs


def bconf_heatmap(df, fname, save_path, base="T", label_offset=0.05):
    # define list for axes ticks to inforce label order,
    # so its the same as the paper
    xaxis = [
        "GG",
        "GA",
        "AG",
        "AA",
        "GC",
        f"G{base}",
        f"A{base}",
        "AC",
        "CA",
        f"{base}A",
        f"{base}G",
        "CG",
        "CC",
        f"C{base}",
        f"{base}C",
        f"{base}{base}"]
    yaxis = xaxis.copy()
    tetramer_order = pd.DataFrame(
        [b.join(f) for f in yaxis for b in xaxis],
        columns=["tetramer"])
    df = df.merge(tetramer_order, how="right", on="tetramer")
    colormap = ListedColormap([
        "darkblue",
        "blue",
        "lightblue",
        "lightgreen",
        "lime",
        "orange",
        "red",
        "crimson"])
    colormap.set_bad(color="grey")
    # plot
    fig, ax = plt.subplots()
    im = ax.imshow(df["pct"].to_numpy().reshape((16, 16)), cmap=colormap)
    plt.colorbar(im)
    # axes
    xlocs = np.arange(len(xaxis))
    ylocs = np.arange(len(yaxis))
    _ = ax.set_xticks(xlocs)
    _ = ax.set_xticklabels(xaxis)
    _ = ax.set_yticks(ylocs)
    _ = ax.set_yticklabels(yaxis)
    ax.set_title((fname + " conformations").upper())
    # save as pdf
    file_path = pathlib.Path(save_path) / f"{fname}_percentages.pdf"
    fig.savefig(fname=file_path, format="pdf")


def correlation_plot(data, fname, save_path, base="T", label_offset=0.05):
    # define colormap
    cmap = mpl.colors.ListedColormap([
        "blue",
        "cornflowerblue",
        "lightskyblue",
        "white",
        "mistyrose",
        "tomato",
        "red"])
    bounds = [-1.0, -.73, -.53, -.3, .3, .53, .73, 1.0]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    cmap.set_bad(color="gainsboro")

    # reorder dataset
    coordinates = list(set(data.index.get_level_values(0)))
    data = data.loc[coordinates][coordinates].sort_index(
        level=1, axis=0).sort_index(level=1, axis=1)

    for crd1, crd2 in itertools.combinations_with_replacement(
            coordinates,
            r=2):
        crd_data = data.loc[crd1][crd2]

        # plot
        fig, ax = plt.subplots(
            1,
            1,
            dpi=300,
            tight_layout=True)
        im = ax.imshow(crd_data, cmap=cmap, norm=norm, aspect='auto')
        plt.colorbar(im)

        # axes
        units = set(crd_data.index)
        xlocs = np.arange(len(units))
        _ = ax.set_xticks(xlocs)
        _ = ax.set_xticklabels(units, rotation=90)

        ylocs = np.arange(len(units))
        _ = ax.set_yticks(ylocs)
        _ = ax.set_yticklabels(units)
        ax.set_title(f"rows: {crd1} | columns: {crd2}")
        plt.tight_layout()

        # save as pdf
        file_path = pathlib.Path(save_path) / f"{crd1}_{crd2}.pdf"
        fig.savefig(fname=file_path, format="pdf")

        plt.close()

    # plot
    fig, ax = plt.subplots(
        1,
        1,
        dpi=300,
        tight_layout=True)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect='auto')
    plt.colorbar(im)

    # axes
    start = len(data) // (2 * len(coordinates))
    step = 2 * start
    locs = np.arange(start, len(data)-1, step)
    _ = ax.set_xticks(locs)
    _ = ax.set_yticks(locs)
    _ = ax.set_xticklabels(coordinates, rotation=90)
    _ = ax.set_yticklabels(coordinates)

    plt.tight_layout()

    # save as pdf
    file_path = pathlib.Path(save_path) / f"{fname}.pdf"
    fig.savefig(fname=file_path, format="pdf")


def basepair_plot(
        data,
        fname,
        save_path,
        base="T",
        label_offset=0.05):
    # define colormap
    cmap = mpl.colors.ListedColormap([
        "blue",
        "cornflowerblue",
        "lightskyblue",
        "white",
        "mistyrose",
        "tomato",
        "red"])
    bounds = [-.6, -.5, -.4, -.3, .3, .4, .5, .6]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    cmap.set_bad(color="gainsboro")

    category = data.index.to_series().apply(lambda s: s[1:3])
    data["category"] = category

    for cat in category.unique():
        cat_df = data[data["category"] == cat]
        cat_df = cat_df.drop("category", axis=1)
        # plot
        fig, ax = plt.subplots(
            1,
            1,
            dpi=300,
            figsize=(7.5, 5),
            tight_layout=True)
        im = ax.imshow(cat_df, cmap=cmap, norm=norm, aspect='auto')
        plt.colorbar(im)

        # axes
        xlocs = np.arange(len(cat_df.columns))
        _ = ax.set_xticks(xlocs)
        _ = ax.set_xticklabels(cat_df.columns.to_list(), rotation=90)

        ylocs = np.arange(len(cat_df.index))
        _ = ax.set_yticks(ylocs)
        _ = ax.set_yticklabels(cat_df.index.to_list())

        ax.set_title(
            f"Correlation for basepair group {cat}")
        plt.tight_layout()

        # save as pdf
        file_path = pathlib.Path(save_path) / f"{cat}.pdf"
        fig.savefig(fname=file_path, format="pdf")

        plt.close()

    data = data.sort_values(by="category")
    # cat_count = category.value_counts()
    # category = category.unique()
    # category.sort()
    data = data.drop("category", axis=1)

    # plot
    fig, ax = plt.subplots(
        1,
        1,
        dpi=300,
        figsize=(7.5, 5),
        tight_layout=True)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect='auto')
    plt.colorbar(im)

    # axes
    xlocs = np.arange(len(data.columns))
    _ = ax.set_xticks(xlocs)
    _ = ax.set_xticklabels(data.columns.to_list(), rotation=90)

    # if yaxis:
    # y_positions = [cat_count[category[i]] for i in range(len(category))]
    # ylocs = np.cumsum(y_positions)
    # _ = ax.set_yticks(ylocs)
    # _ = ax.set_yticklabels(category)
    # else:
    # _ = ax.set_yticklabels([])

    ax.set_title("Correlation for all basepairs")
    plt.tight_layout()

    # save as pdf
    file_path = pathlib.Path(save_path) / f"{fname}.pdf"
    fig.savefig(fname=file_path, format="pdf")
