# vt - Simple västtrafik command-line client

This is a simple, quick-and-dirty command-line application to look up
trips with the Swedish public transport agency västtrafik. This
was written in a few hours, so expect to encounter some bugs.

*Note: An authorization key for the västtrafik API is required. See
[their website](http://labs.vasttrafik.se/) for information on
obtaining one. The key then needs to be specified in the configuration
file (see below).*

## Installation

This application can be installed using python's
[setuptools](https://pypi.python.org/pypi/setuptools). To do so, run
`python setup.py install` as root. This will fetch and install all
python libraries this application depends on. Refer to the setuptools
documentation for more installation options.

If you prefer not to use setuptools, you can install the dependencies yourself and
put the vt.py script somewhere in your `$PATH`.

## Dependencies

This application has only been tested with python3. It might work
with python2 as well, but I haven't tried.

Additionally, the following python libraries are used:

- [colorama](https://pypi.python.org/pypi/colorama)
- [PyXDG](http://freedesktop.org/wiki/Software/pyxdg/)
- [tabulate](https://pypi.python.org/pypi/tabulate)
- [requests](http://docs.python-requests.org/en/latest/)

## Usage

From the program's help output:

    Usage: vt [options] FROM TO
           vt [options] TO
           vt [options]
    
    Options:
      -h, --help            show this help message and exit
      -s, --short           Show only trip summaries.
      -t TIME, --time=TIME  Time of departure
      -d DATE, --date=DATE  Date of departure
      -r, --raw             Print raw JSON data.
      -c, --complete        Show possible completions for stop name instead of
                            searching for trips (mainly used by ZSH completion)
      -v, --verbose         Print debug output.

When called with two arguments, information about the next trips from `FROM` to `TO`
will be printed. Using one or zero arguments will attempt to read default origin
and destinations from the configuration file and display the trips accordingly.

## Configuration

Basic configuration is possible by providing a
`$XDG_CONFIG_HOME/vt/config.py` file (defaults to
`~/.config/vt/config.py` if `$XDG_CONFIG_HOME` is not set). A sample
configuration file is provided in this repository.

Note that the configuration file is ordinary python code. For example,
default origin and destination can be set depending host names or
time. The following example shows how to set different default
locations based on the host name:

    if host == "atlas":
        default_origin = "Backa Kyrkogata"
        default_destination = "Chalmers Tvärgata"
    else:
        default_destination = "Backa Kyrkogata"
        default_origin = "Chalmers Tvärgata"

## ZSH completion

Optionally, a ZSH completion function for stop names is provided in
the `_vt` file. This file needs to be placed in a directory for zsh
completions in order for it to be used. See the
[zsh documentation](http://zsh.sourceforge.net/Doc/Release/Completion-System.html)
for details on how to do this.

The completion function assumes that the `vt` script is
available somewhere in your `$PATH`.

## Sample output

    $ vt Brunnsparken Chalmers
    Time        Stop                               Time        Stop
    ----------  ---------------  ----------------  ----------  -----------
    (18:58 +1)  Brunnsparken[E]  --[7, 00:10]-->   (19:08 +1)  Chalmers[B]
    (19:00)     Brunnsparken[E]  --[6, 00:18]-->   (19:18)     Chalmers[A]
    (19:01 +1)  Brunnsparken[A]  --[10, 00:10]-->  (19:11 +1)  Chalmers[B]
    (19:03 +3)  Brunnsparken[E]  --[16, 00:07]-->  (19:10 +5)  Chalmers[B]
    (19:08 +3)  Brunnsparken[E]  --[7, 00:10]-->   (19:18 +3)  Chalmers[B]

    $ vt Brunnsbotorget Chalmers -t 20:00
    Time     Stop                             Time     Stop
    -------  -----------------  ------------  -------  -----------
    (20:00)  Brunnsbotorget[A]  --[00:21]-->  (20:21)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    	| (20:00)     Brunnsbotorget[A]     --[19, 00:09]-->  (20:09)  Kungsportsplatsen[D]
    	| (20:16 -1)  Kungsportsplatsen[D]  --[16, 00:05]-->  (20:21)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    (20:10)  Brunnsbotorget[A]  --[00:21]-->  (20:31)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    	| (20:10)     Brunnsbotorget[A]     --[18, 00:09]-->  (20:19)  Kungsportsplatsen[D]
    	| (20:26 -1)  Kungsportsplatsen[D]  --[16, 00:05]-->  (20:31)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    (20:13)  Brunnsbotorget[B]  --[00:24]-->  (20:37)  Chalmers[B]
    	* -------  -----------------  ----------------  -------  ------------
    	| (20:13)  Brunnsbotorget[B]  --[52, 00:15]-->  (20:28)  Korsvägen[A]
    	| (20:34)  Korsvägen[A]       --[10, 00:03]-->  (20:37)  Chalmers[B]
    	* -------  -----------------  ----------------  -------  ------------
    (20:20)  Brunnsbotorget[A]  --[00:26]-->  (20:46)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    	| (20:20)     Brunnsbotorget[A]     --[19, 00:09]-->  (20:29)  Kungsportsplatsen[D]
    	| (20:41 -1)  Kungsportsplatsen[D]  --[16, 00:05]-->  (20:46)  Chalmers[B]
    	* ----------  --------------------  ----------------  -------  --------------------
    (20:28)  Brunnsbotorget[B]  --[00:23]-->  (20:51)  Chalmers[B]
    	* -------  -----------------  ----------------  -------  ------------
    	| (20:28)  Brunnsbotorget[B]  --[52, 00:15]-->  (20:43)  Korsvägen[A]
    	| (20:48)  Korsvägen[A]       --[10, 00:03]-->  (20:51)  Chalmers[B]
    	* -------  -----------------  ----------------  -------  ------------

## License

This program is licensed under the GNU General Public License
Version 2. See the `LICENSE` file for details.
