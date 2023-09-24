import pytest
from pathlib import Path
import os
import json
import numpy as np
import spikeinterface as si
import spikeinterface.extractors as se
from spikeinterface.extractors import read_mearec
from spikeinterface import set_global_tmp_folder
from spikeinterface.postprocessing import (
    compute_correlograms,
    compute_unit_locations,
    compute_template_similarity,
    compute_spike_amplitudes,
)
from spikeinterface.curation import apply_sortingview_curation

if hasattr(pytest, "global_test_folder"):
    cache_folder = pytest.global_test_folder / "curation"
else:
    cache_folder = Path("cache_folder") / "curation"
parent_folder = Path(__file__).parent
ON_GITHUB = bool(os.getenv("GITHUB_ACTIONS"))
KACHERY_CLOUD_SET = bool(os.getenv("KACHERY_CLOUD_CLIENT_ID")) and bool(os.getenv("KACHERY_CLOUD_PRIVATE_KEY"))


set_global_tmp_folder(cache_folder)


# this needs to be run only once
def generate_sortingview_curation_dataset():
    import spikeinterface.widgets as sw

    local_path = si.download_dataset(remote_path="mearec/mearec_test_10s.h5")
    recording, sorting = read_mearec(local_path)

    we = si.extract_waveforms(recording, sorting, folder=None, mode="memory")

    _ = compute_spike_amplitudes(we)
    _ = compute_correlograms(we)
    _ = compute_template_similarity(we)
    _ = compute_unit_locations(we)

    # plot_sorting_summary with curation
    w = sw.plot_sorting_summary(we, curation=True, backend="sortingview")

    # curation_link:
    # https://figurl.org/f?v=gs://figurl/spikesortingview-10&d=sha1://bd53f6b707f8121cadc901562a89b67aec81cc81&label=SpikeInterface%20-%20Sorting%20Summary


@pytest.mark.skipif(ON_GITHUB and not KACHERY_CLOUD_SET, reason="Kachery cloud secrets not available")
def test_gh_curation():
    local_path = si.download_dataset(remote_path="mearec/mearec_test_10s.h5")
    _, sorting = read_mearec(local_path)

    # from GH
    # curated link:
    # https://figurl.org/f?v=gs://figurl/spikesortingview-10&d=sha1://bd53f6b707f8121cadc901562a89b67aec81cc81&label=SpikeInterface%20-%20Sorting%20Summary&s={%22sortingCuration%22:%22gh://alejoe91/spikeinterface/fix-codecov/spikeinterface/curation/tests/sv-sorting-curation.json%22}
    gh_uri = "gh://SpikeInterface/spikeinterface/main/src/spikeinterface/curation/tests/sv-sorting-curation.json"
    sorting_curated_gh = apply_sortingview_curation(sorting, uri_or_json=gh_uri, verbose=True)
    print(f"From GH: {sorting_curated_gh}")

    assert len(sorting_curated_gh.unit_ids) == 9
    assert "#8-#9" in sorting_curated_gh.unit_ids
    assert "accept" in sorting_curated_gh.get_property_keys()
    assert "mua" in sorting_curated_gh.get_property_keys()
    assert "artifact" in sorting_curated_gh.get_property_keys()

    sorting_curated_gh_accepted = apply_sortingview_curation(sorting, uri_or_json=gh_uri, include_labels=["accept"])
    sorting_curated_gh_mua = apply_sortingview_curation(sorting, uri_or_json=gh_uri, exclude_labels=["mua"])
    sorting_curated_gh_art_mua = apply_sortingview_curation(
        sorting, uri_or_json=gh_uri, exclude_labels=["artifact", "mua"]
    )
    assert len(sorting_curated_gh_accepted.unit_ids) == 3
    assert len(sorting_curated_gh_mua.unit_ids) == 6
    assert len(sorting_curated_gh_art_mua.unit_ids) == 5


@pytest.mark.skipif(ON_GITHUB and not KACHERY_CLOUD_SET, reason="Kachery cloud secrets not available")
def test_sha1_curation():
    local_path = si.download_dataset(remote_path="mearec/mearec_test_10s.h5")
    _, sorting = read_mearec(local_path)

    # from SHA1
    # curated link:
    # https://figurl.org/f?v=gs://figurl/spikesortingview-10&d=sha1://bd53f6b707f8121cadc901562a89b67aec81cc81&label=SpikeInterface%20-%20Sorting%20Summary&s={%22sortingCuration%22:%22sha1://1182ba19671fcc7d3f8e0501b0f8c07fb9736c22%22}
    sha1_uri = "sha1://1182ba19671fcc7d3f8e0501b0f8c07fb9736c22"
    sorting_curated_sha1 = apply_sortingview_curation(sorting, uri_or_json=sha1_uri, verbose=True)
    print(f"From SHA: {sorting_curated_sha1}")

    assert len(sorting_curated_sha1.unit_ids) == 9
    assert "#8-#9" in sorting_curated_sha1.unit_ids
    assert "accept" in sorting_curated_sha1.get_property_keys()
    assert "mua" in sorting_curated_sha1.get_property_keys()
    assert "artifact" in sorting_curated_sha1.get_property_keys()

    sorting_curated_sha1_accepted = apply_sortingview_curation(sorting, uri_or_json=sha1_uri, include_labels=["accept"])
    sorting_curated_sha1_mua = apply_sortingview_curation(sorting, uri_or_json=sha1_uri, exclude_labels=["mua"])
    sorting_curated_sha1_art_mua = apply_sortingview_curation(
        sorting, uri_or_json=sha1_uri, exclude_labels=["artifact", "mua"]
    )
    assert len(sorting_curated_sha1_accepted.unit_ids) == 3
    assert len(sorting_curated_sha1_mua.unit_ids) == 6
    assert len(sorting_curated_sha1_art_mua.unit_ids) == 5


def test_json_curation():
    local_path = si.download_dataset(remote_path="mearec/mearec_test_10s.h5")
    _, sorting = read_mearec(local_path)

    # from curation.json
    json_file = parent_folder / "sv-sorting-curation.json"
    sorting_curated_json = apply_sortingview_curation(sorting, uri_or_json=json_file, verbose=True)
    print(f"Sorting: {sorting.get_unit_ids()}")
    print(f"From JSON: {sorting_curated_json}")

    assert len(sorting_curated_json.unit_ids) == 9
    print(sorting_curated_json.unit_ids)
    assert "#8-#9" in sorting_curated_json.unit_ids
    assert "accept" in sorting_curated_json.get_property_keys()
    assert "mua" in sorting_curated_json.get_property_keys()
    assert "artifact" in sorting_curated_json.get_property_keys()

    sorting_curated_json_accepted = apply_sortingview_curation(
        sorting, uri_or_json=json_file, include_labels=["accept"]
    )
    sorting_curated_json_mua = apply_sortingview_curation(sorting, uri_or_json=json_file, exclude_labels=["mua"])
    sorting_curated_json_mua1 = apply_sortingview_curation(
        sorting, uri_or_json=json_file, exclude_labels=["artifact", "mua"]
    )
    assert len(sorting_curated_json_accepted.unit_ids) == 3
    assert len(sorting_curated_json_mua.unit_ids) == 6
    assert len(sorting_curated_json_mua1.unit_ids) == 5


def test_false_positive_curation():
    # https://spikeinterface.readthedocs.io/en/latest/modules_gallery/core/plot_2_sorting_extractor.html
    sampling_frequency = 30000.0
    duration = 20.0
    num_timepoints = int(sampling_frequency * duration)
    num_units = 20
    num_spikes = 1000
    times0 = np.int_(np.sort(np.random.uniform(0, num_timepoints, num_spikes)))
    labels0 = np.random.randint(1, num_units + 1, size=num_spikes)
    times1 = np.int_(np.sort(np.random.uniform(0, num_timepoints, num_spikes)))
    labels1 = np.random.randint(1, num_units + 1, size=num_spikes)

    sorting = se.NumpySorting.from_times_labels([times0, times1], [labels0, labels1], sampling_frequency)
    print("Sorting: {}".format(sorting.get_unit_ids()))

    # Test curation JSON:
    test_json = {"labelsByUnit": {"1": ["accept"], "2": ["artifact"], "12": ["artifact"]}, "mergeGroups": [[2, 12]]}

    json_path = "test_data.json"
    with open(json_path, "w") as f:
        json.dump(test_json, f, indent=4)

    sorting_curated_json = apply_sortingview_curation(sorting, uri_or_json=json_path, verbose=True)
    accept_idx = np.where(sorting_curated_json.get_property("accept"))[0]
    sorting_curated_ids = sorting_curated_json.get_unit_ids()
    print(f"Accepted unit IDs: {sorting_curated_ids[accept_idx]}")

    # Check if unit_id 1 has received the "accept" label.
    assert sorting_curated_json.get_unit_property(unit_id=1, key="accept")
    # Check if unit_id 10 has received the "accept" label.
    # If so, test fails since only unit_id 1 received the "accept" label in test_json.
    assert not sorting_curated_json.get_unit_property(unit_id=10, key="accept")
    print(sorting_curated_json.unit_ids)
    # Merging unit_ids of dtype int creates a new unit id
    assert 21 in sorting_curated_json.unit_ids


if __name__ == "__main__":
    # generate_sortingview_curation_dataset()
    test_sha1_curation()
    test_gh_curation()
    test_json_curation()
    test_false_positive_curation()
