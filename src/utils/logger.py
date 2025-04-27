import logging
import os
import sys

class Logger:
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    cyan = "\x1b[36;20m"
    purple = "\x1b[35;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"

    @staticmethod
    def Info(message):
        print("") # Reason? --> sys.stdout.flush() in progress bar
        print(Logger.cyan + "[INFO] " + Logger.reset + message)

    @staticmethod
    def Debug(message):
        print("") # Reason? --> sys.stdout.flush() in progress bar
        print(Logger.purple + "[DEBUG] " + Logger.reset + message)

    @staticmethod
    def Warning(message):
        print("") # Reason? --> sys.stdout.flush() in progress bar
        print(Logger.yellow + "[WARNING] " + Logger.reset + message)

    @staticmethod
    def Error(message):
        print("") # Reason? --> sys.stdout.flush() in progress bar
        print(Logger.red + "[ERROR] " + Logger.reset + message)

    @staticmethod
    def Critical(message):
        print("") # Reason? --> sys.stdout.flush() in progress bar
        print(Logger.bold_red + "[CRITICAL] " + Logger.reset +  message)

    @staticmethod
    def ProgressBar(iteration, total, bar_length=100):
        iteration += 1

        if total < iteration:
            print("")
            Logger.Critical("Number of iterations is less than the total number of iterations.")
            return

        percent = float(iteration) / float(total)
        arrow = '-' * int(round(percent * bar_length) - 1)
        spaces = ' ' * (bar_length - len(arrow))

        sys.stdout.write(f"\rProgress: \x1b[32;20m[{arrow}{spaces}]\x1b[0m {int(percent * 100)}% - {iteration}/{total}")
        sys.stdout.flush()

        if iteration == total:
            print("")
