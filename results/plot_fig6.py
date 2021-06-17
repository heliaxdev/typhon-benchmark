
from re import findall, search, split
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from glob import glob
from itertools import cycle
import matplotlib.ticker as ticker


# FuncFormatter can be used as a decorator
@ticker.FuncFormatter
def major_formatter(x, pos):
    return f"{x/1000:0.0f}k"

def major_formatter_sec(x, pos):
    return f"{x/1000:0.1f}"

class PlotError(Exception):
    pass

markers = cycle(['o', 'v', 's', 'd'])
styles = cycle(['solid', 'dashed', 'dashdot', 'dotted'])

class Ploter:
    def __init__(self, filenames):
        if not filenames:
            raise PlotError('No data to plot')

        self.results = []
        try:
            for filename in filenames:
                with open(filename, 'r') as f:
                    self.results += [f.read().replace(',', '')]
        except OSError as e:
            raise PlotError(f'Failed to load log files: {e}')

    def _natural_keys(self, text):
        def try_cast(text): return int(text) if text.isdigit() else text
        return [try_cast(c) for c in split('(\d+)', text)]

    def _tps(self, data):
        values = findall(r' TPS: (\d+) \+/- (\d+)', data)
        values = [(int(x), int(y)) for x, y in values]
        return list(zip(*values))

    def _latency(self, data, scale=1):
        values = findall(r' Latency: (\d+) \+/- (\d+)', data)
        values = [(float(x)/scale, float(y)/scale) for x, y in values]
        return list(zip(*values))

    def _variable(self, data):
        return [int(x) for x in findall(r'Variable value: X=(\d+)', data)]

    def _nodes(self, data, system):
        x = search(r'Committee size: (\d+)', data).group(1)
        f = search(r'Faults: (\d+)', data).group(1)
        faults = f'({f} faulty)' if f != '0' else ''
        return f'{system} - {x} validators {faults}'

    def plot_latency(self, name, new=True):
        if new:
            plt.figure(figsize=[15.4, 4])

        style = next(styles)
        self.results.sort(key=self._natural_keys)
        for result in self.results:
            y_values, y_err = self._latency(result)
            x_values = self._variable(result)
            if len(y_values) != len(y_err) or len(y_err) != len(x_values):
                raise PlotError('Unequal number of x, y, and y_err values')

            try:
                label = self._nodes(result, name)
            except:
                # Skip if no specific committee size
                continue

            plt.errorbar(
                x_values, y_values, yerr=y_err,  # uplims=True, lolims=True,
                label=label,
                marker=next(markers), linestyle=style
            )

        plt.legend(loc='upper left', ncol=4)
        plt.xlim(xmin=0, xmax=180000)
        plt.ylim(bottom=0, top=15000)
        plt.xlabel('Throughput (tx/s)')
        plt.ylabel('Latency (s)')
        plt.grid(True, which='both')
        ax = plt.gca()
        ax.xaxis.set_major_formatter(major_formatter)
        ax.yaxis.set_major_formatter(major_formatter_sec)

if __name__ == '__main__':
    new = True
    names = ['Narwhal-HS', 'Baseline-HS', 'Batched-HS', 'Tusk',]
    for system, name in zip(['HS-on-Dag', 'Baseline HS', 'Batched HS', 'Tusk'], names):
        files = glob(f'data/{system}/aggregated/committee_wihtout_4/*.txt')
        plot = Ploter(files).plot_latency(name, new)
        new = False

    for x in ['pdf', 'png']:
        plt.savefig(f'figures/latency.{x}', bbox_inches='tight')