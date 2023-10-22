import matplotlib.pyplot as plt
import os

class Visualization:
    def __init__(self, path, dpi):
            self._path = path
            self._dpi = dpi


    def save_data_and_plot(self, data, filename, xlabel, ylabel):
        """
        Produce a plot of performance of the agent over the session and save the relative data to txt
        """
        min_val = min(data)
        max_val = max(data)

        plt.rcParams.update({'font.size': 24})  # set bigger font size

        plt.plot(data)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.margins(0)
        plt.ylim(min_val - 0.05 * abs(min_val), max_val + 0.05 * abs(max_val))
        fig = plt.gcf()
        fig.set_size_inches(20, 11.25)
        fig.savefig(os.path.join(self._path, 'plot_'+filename+'.png'), dpi=self._dpi)
        plt.close("all")

        with open(os.path.join(self._path, 'plot_'+filename + '_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)
    

    def save_data_and_plot2(self, data, data2, filename, xlabel, ylabel):
        """
        Produce a plot of performance of the agent over the session and save the relative data to txt
        """
        min_val1 = min(data)
        max_val1 = max(data)
        min_val2 = min(data2)
        max_val2 = max(data2)

        min_val = min(min_val1, min_val2)
        max_val = max(max_val1, max_val2)

        plt.rcParams.update({'font.size': 24})  # set bigger font size

        plt.plot(data)
        plt.plot(data2)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.margins(0)
        plt.ylim(min_val - 0.05 * abs(min_val), max_val + 0.05 * abs(max_val))
        fig = plt.gcf()
        fig.set_size_inches(20, 11.25)
        fig.savefig(os.path.join(os.getcwd(), 'plot_'+filename+'.png'), dpi=self._dpi)
        plt.close("all")

        with open(os.path.join(os.getcwd(), 'plot_'+filename + '_data.txt'), "w") as file:
            for value in data:
                    file.write("%s\n" % value)