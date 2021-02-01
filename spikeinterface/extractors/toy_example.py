import numpy as np
from pathlib import Path

from spikeinterface.extractors import NumpyRecording, NumpySorting


def toy_example(duration=10, num_channels=4, num_units=10,
                sampling_frequency=30000.0, num_segments=2,
                average_peak_amplitude=-100, upsamplefac=13,
                dumpable=False, dump_folder=None, seed=None):
    '''
    Creates toy recording and sorting extractors.

    Parameters
    ----------
    duration: float (or list if multi segment)
        Duration in s (default 10)
    num_channels: int
        Number of channels (default 4)
    num_units: int
        Number of units (default 10)
    sampling_frequency: float
        Sampling frequency (default 30000)
    num_segments: int default 2
        Number of segments.
    dumpable: bool
        If True, objects are dumped to file and become 'dumpable'
    dump_folder: str or Path
        Path to dump folder (if None, 'test' is used
    seed: int
        Seed for random initialization

    Returns
    -------
    recording: RecordingExtractor
        The output recording extractor. If dumpable is False it's a NumpyRecordingExtractor, otherwise it's an
        MdaRecordingExtractor
    sorting: SortingExtractor
        The output sorting extractor. If dumpable is False it's a NumpyRecordingExtractor, otherwise it's an
        NpzSortingExtractor
    '''
    
    if isinstance(duration, int):
        duration = float(duration)
    
    if isinstance(duration, float):
        durations = [duration] * num_segments
    else:
        durations = duration
        assert isinstance(duration, list)
        assert len(durations) == num_segments
        assert all(isinstance(d, float) for d in durations)
    
    
    waveforms, geom = synthesize_random_waveforms(K=num_units, M=num_channels,
                        average_peak_amplitude=average_peak_amplitude, upsamplefac=upsamplefac, seed=seed)
    
    unit_ids = np.arange(num_units, dtype='int64')
    
    traces_list = []
    times_list = []
    labels_list = []
    for segment_index in range(num_segments):
        times, labels = synthesize_random_firings(K=num_units, duration=duration, sampling_frequency=sampling_frequency, seed=seed)
        times_list.append(times)
        labels_list.append(labels)

        traces = synthesize_timeseries(times, labels, unit_ids, waveforms, sampling_frequency, duration,
                                noise_level=10, waveform_upsamplefac=upsamplefac, seed=seed)
        traces_list.append(traces)
                                  

    
    sorting = NumpySorting.from_times_labels(times_list, labels_list, sampling_frequency)
    recording = NumpyRecording(traces_list, sampling_frequency)
    recording.annotate(is_filtered=True)
    
    #~ if dumpable:
        #~ if dump_folder is None:
            #~ dump_folder = 'toy_example'
        #~ dump_folder = Path(dump_folder)

        #~ se.MdaRecordingExtractor.write_recording(RX, dump_folder)
        #~ RX = se.MdaRecordingExtractor(dump_folder)
        #~ se.NpzSortingExtractor.write_sorting(SX, dump_folder / 'sorting.npz')
        #~ SX = se.NpzSortingExtractor(dump_folder / 'sorting.npz')

    return recording, sorting



def synthesize_random_firings(K=20, sampling_frequency=30000.0, duration=60, seed=None):
    if seed is not None:
        np.random.seed(seed)
        seeds = np.random.RandomState(seed=seed).randint(0, 2147483647, K)
    else:
        seeds = np.random.randint(0, 2147483647, K)

    firing_rates = 3 * np.ones((K))
    refr = 4

    N = np.int64(duration * sampling_frequency)

    # events/sec * sec/timepoint * N
    populations = np.ceil(firing_rates / sampling_frequency * N).astype('int')
    #~ print(populations)
    times = np.zeros(0)
    labels = np.zeros(0, dtype='int64')

    #~ for i, k in enumerate(range(1, K + 1)):
    times = []
    labels = []
    
    for unit_id in range(K):
        refr_timepoints = refr / 1000 * sampling_frequency

        times0 = np.random.rand(populations[unit_id]) * (N - 1) + 1

        ## make an interesting autocorrelogram shape
        times0 = np.hstack((times0, times0 + rand_distr2(refr_timepoints, refr_timepoints * 20, times0.size, seeds[unit_id])))
        times0 = times0[np.random.RandomState(seed=seeds[unit_id]).choice(times0.size, int(times0.size / 2))]
        times0 = times0[(0 <= times0) & (times0 < N)]

        times0 = enforce_refractory_period(times0, refr_timepoints)
        labels0 = np.ones(times0.size,dtype='int64')
        
        times.append(times0.astype('int64'))
        labels.append(labels0)
        
    times = np.concatenate(times)
    labels = np.concatenate(labels)

    sort_inds = np.argsort(times)
    times = times[sort_inds]
    labels = labels[sort_inds]

    return (times, labels)


def rand_distr2(a, b, num, seed):
    X = np.random.RandomState(seed=seed).rand(num)
    X = a + (b - a) * X ** 2
    return X


def enforce_refractory_period(times_in, refr):
    if (times_in.size == 0): return times_in

    times0 = np.sort(times_in)
    done = False
    while not done:
        diffs = times0[1:] - times0[:-1]
        diffs = np.hstack((diffs, np.inf))  # hack to make sure we handle the last one
        inds0 = np.where((diffs[:-1] <= refr) & (diffs[1:] >= refr))[0]  # only first violator in every group
        if len(inds0) > 0:
            times0[inds0] = -1  # kind of a hack, what's the better way?
            times0 = times0[np.where(times0 >= 0)]
        else:
            done = True

    return times0





def synthesize_random_waveforms(M=5, T=500, K=20, upsamplefac=13, timeshift_factor=3, average_peak_amplitude=-10,
                                seed=None):
    if seed is not None:
        np.random.seed(seed)
        seeds = np.random.RandomState(seed=seed).randint(0, 2147483647, K)
    else:
        seeds = np.random.randint(0, 2147483647, K)
    geometry = None
    avg_durations = [200, 10, 30, 200]
    avg_amps = [0.5, 10, -1, 0]
    rand_durations_stdev = [10, 4, 6, 20]
    rand_amps_stdev = [0.2, 3, 0.5, 0]
    rand_amp_factor_range = [0.5, 1]
    geom_spread_coef1 = 0.2
    geom_spread_coef2 = 1

    if not geometry:
        geometry = np.zeros((2, M))
        geometry[0, :] = np.arange(1, M + 1)

    geometry = np.array(geometry)
    avg_durations = np.array(avg_durations)
    avg_amps = np.array(avg_amps)
    rand_durations_stdev = np.array(rand_durations_stdev)
    rand_amps_stdev = np.array(rand_amps_stdev)
    rand_amp_factor_range = np.array(rand_amp_factor_range)

    neuron_locations = get_default_neuron_locations(M, K, geometry)

    ## The waveforms_out
    WW = np.zeros((M, T * upsamplefac, K))

    for i, k in enumerate(range(1, K + 1)):
        for m in range(1, M + 1):
            diff = neuron_locations[:, k - 1] - geometry[:, m - 1]
            dist = np.sqrt(np.sum(diff ** 2))
            durations0 = np.maximum(np.ones(avg_durations.shape),
                                    avg_durations + np.random.RandomState(seed=seeds[i]).randn(1, 4) * rand_durations_stdev) * upsamplefac
            amps0 = avg_amps + np.random.RandomState(seed=seeds[i]).randn(1, 4) * rand_amps_stdev
            waveform0 = synthesize_single_waveform(N=T * upsamplefac, durations=durations0, amps=amps0)
            waveform0 = np.roll(waveform0, int(timeshift_factor * dist * upsamplefac))
            waveform0 = waveform0 * np.random.RandomState(seed=seeds[i]).uniform(rand_amp_factor_range[0], rand_amp_factor_range[1])
            WW[m - 1, :, k - 1] = waveform0 / (geom_spread_coef1 + dist * geom_spread_coef2)

    peaks = np.max(np.abs(WW), axis=(0, 1))
    WW = WW / np.mean(peaks) * average_peak_amplitude

    return (WW, geometry.T)


def get_default_neuron_locations(M, K, geometry):
    num_dims = geometry.shape[0]
    neuron_locations = np.zeros((num_dims, K))
    for k in range(1, K + 1):
        if K > 0:
            ind = (k - 1) / (K - 1) * (M - 1) + 1
            ind0 = int(ind)
            if ind0 == M:
                ind0 = M - 1
                p = 1
            else:
                p = ind - ind0
            if M > 0:
                neuron_locations[:, k - 1] = (1 - p) * geometry[:, ind0 - 1] + p * geometry[:, ind0]
            else:
                neuron_locations[:, k - 1] = geometry[:, 0]
        else:
            neuron_locations[:, k - 1] = geometry[:, 0]

    return neuron_locations



def exp_growth(amp1, amp2, dur1, dur2):
    t = np.arange(0, dur1)
    Y = np.exp(t / dur2)
    # Want Y[0]=amp1
    # Want Y[-1]=amp2
    Y = Y / (Y[-1] - Y[0]) * (amp2 - amp1)
    Y = Y - Y[0] + amp1;
    return Y


def exp_decay(amp1, amp2, dur1, dur2):
    Y = exp_growth(amp2, amp1, dur1, dur2)
    Y = np.flipud(Y)
    return Y


def smooth_it(Y, t):
    Z = np.zeros(Y.size)
    for j in range(-t, t + 1):
        Z = Z + np.roll(Y, j)
    return Z


def synthesize_single_waveform(N=800, durations=[200, 10, 30, 200], amps=[0.5, 10, -1, 0]):
    durations = np.array(durations).ravel()
    if (np.sum(durations) >= N - 2):
        durations[-1] = N - 2 - np.sum(durations[0:durations.size - 1])

    amps = np.array(amps).ravel()

    timepoints = np.round(np.hstack((0, np.cumsum(durations) - 1))).astype('int');

    t = np.r_[0:np.sum(durations) + 1]

    Y = np.zeros(len(t))
    Y[timepoints[0]:timepoints[1] + 1] = exp_growth(0, amps[0], timepoints[1] + 1 - timepoints[0], durations[0] / 4)
    Y[timepoints[1]:timepoints[2] + 1] = exp_growth(amps[0], amps[1], timepoints[2] + 1 - timepoints[1], durations[1])
    Y[timepoints[2]:timepoints[3] + 1] = exp_decay(amps[1], amps[2], timepoints[3] + 1 - timepoints[2],
                                                   durations[2] / 4)
    Y[timepoints[3]:timepoints[4] + 1] = exp_decay(amps[2], amps[3], timepoints[4] + 1 - timepoints[3],
                                                   durations[3] / 5)
    Y = smooth_it(Y, 3)
    Y = Y - np.linspace(Y[0], Y[-1], len(t))
    Y = np.hstack((Y, np.zeros(N - len(t))))
    Nmid = int(np.floor(N / 2))
    peakind = np.argmax(np.abs(Y))
    Y = np.roll(Y, Nmid - peakind)

    return Y

def synthesize_timeseries(spike_times, spike_labels, unit_ids, waveforms, sampling_frequency, duration,
                                noise_level=10, waveform_upsamplefac=13, seed=None):
    
    num_timepoints = np.int64(sampling_frequency * duration)
    waveform_upsamplefac = int(waveform_upsamplefac)
    W = waveforms

    M, TT, K = W.shape[0], W.shape[1], W.shape[2]
    T = int(TT / waveform_upsamplefac)
    Tmid = int(np.ceil((T + 1) / 2 - 1))

    N = num_timepoints

    if seed is not None:
        X = np.random.RandomState(seed=seed).randn(M, N) * noise_level
    else:
        X = np.random.randn(M, N) * noise_level

    for k0 in unit_ids:
        waveform0 = waveforms[:, :, k0 - 1]
        times0 = spike_times[spike_labels == k0]
        
        for t0 in times0:
            amp0 = 1
            frac_offset = int(np.floor((t0 - np.floor(t0)) * waveform_upsamplefac))
            tstart = np.int64(np.floor(t0)) - Tmid
            if (0 <= tstart) and (tstart + T <= N):
                X[:, tstart:tstart + T] = X[:, tstart:tstart + T] + waveform0[:,
                                                                    frac_offset::waveform_upsamplefac] * amp0

    return X


#~ if __name__ == '__main__':
    #~ rec, sorting = toy_example(num_segments=2)

