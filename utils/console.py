# adapted from https://twistedmatrix.com/documents/current/_downloads/stdiodemo.py

from twisted.internet import stdio, reactor
from twisted.protocols import basic
"""
A basic user console
"""


class Console(basic.LineReceiver):

    delimiter = '\n'  # unix terminal style newlines. remove this line

    # for use with Telnet
    def connectionMade(self):
        self.sendLine("Command line interface. Type 'help' for help.")
        self.transport.write('>>> ')

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()

    def lineReceived(self, line):
        # Ignore blank lines
        if not line: return

        # Parse the command
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        res = None
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError, e:
            self.sendLine('Error: no such command.')
        else:
            try:
                method(*args)
            except Exception, e:
                self.sendLine('Error: ' + str(e))

        self.transport.write('>>> ')

    def printResult(self, res):
        if res is not None:
            self.sendLine(str(res))
        self.transport.write('>>> ')

    def do_help(self, command=None):
        """help [command]: List commands, or show help on the given command"""
        if command:
            self.sendLine(getattr(self, 'do_' + command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.sendLine("Valid commands: " + " ".join(commands))

    def do_echo(self, message):
        """echo [message]: repeat input message"""
        if message:
            self.printResult(message)

    def do_quit(self):
        """quit: Quit this session"""
        self.sendLine('Goodbye.')
        self.transport.loseConnection()


if __name__ == "__main__":
    stdio.StandardIO(Plugin())
    reactor.run()