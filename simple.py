#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# inspired by Andrew Butcher's 'libnetstation' cpp library: [ http://code.google.com/p/libnetstation/ ]     
#

from socket_wrapper import Socket
import struct     
import math
import time # for time in milliseconds
import sys
import exceptions  # sys.

global _ts_last
_ts_last = 0


def _get_endianness_string(_map={'little': 'NTEL', 'big': 'UNIX'}):
    """
    check the endianness of the system
    """
    key = sys.byteorder
    return _map[ key ]


def _cat(*strings):
    """
    concatenate all the strings in a 'packed' string
    """
    args = [s for s in strings if s is not None and len(s) > 0 ]
    fmt_list = []
    for s in args:
        fmt_list.append('%ds' % (len(s),))
    fmt = ''.join(fmt_list)
    result = struct.pack(fmt, *args)
    return result


def p_string(s):
    """
    pack 's' as a single-byte-counter Pascal string
    """
    if s is None:
        return None
    fmt = '%dp' % (len(s) + 1)
    ps = struct.pack(fmt, s)
    return ps

def ms_localtime(warn_me=True):
    """
    gives the local time in milliseconds (modulo 1.000.000.000)
    """
    global _ts_last
    modulo = 1000000
    ms_remainder = int(math.floor((time.time() % modulo) * 1000))

    if warn_me and (ms_remainder < _ts_last):
        raise Eggog("internal 32-bit counter passed through zero, please resynchronize (call .synch() once again)")
    _ts_last = ms_remainder
    return ms_remainder


def truncate_pyint_to_i32_interval(i):
    """
    truncate the value to fit (- 0x80000000 <= value <= 0x7FFFFFFF)
    """
    i_= Eggog.try_as_int(i)
    negative = (i_ < 0)
    if negative:
        ii = -(i_ + 1) # ~ i_
        i_ = ii
    if negative:
        i_ = -i_ - 1
    return i_



def is_32_bit_int_compatible(i):
    """
    check if we can transmit the given number as a signed 32-bit integer
    """
    try:
        if i == truncate_pyint_to_i32_interval(i):
            return True
    except:
        pass
        return False


def _unique(a_list):
        """
        returns list without duplicates
        """
        d = {}
        for e in a_list:
            d[e] = 1
        return d.keys()


def pad_key(k):

    n = len(k)
    d = 4 - n
    if d > 0:
        return  (k + ' ' * d)
    else:
        return k


def make_fit(k):

    n = len(k)
    d = n - 4
    if d > 0:
        return k[0:4]
    else:
        return k


class Eggog(exceptions.Exception):
    """
    general exception, will make things more specific if necessary ;
    at the moment it means that the server has returned an error --
    -- or one of the strings was not a 4-byte one when it should =%:-(
    """

    @staticmethod     
    def check_type(string_key):
        """     
        check if the type of the key is string type --
        -- and raise an exception if it isn't)
        """     
        if isinstance(string_key, type('')):
            return True
        else:
            raise Eggog("'%s': EGI wants the key to be four _characters_ (not %s) !" % (type(string_key),
                                                                                        type(string_key)))

    @staticmethod     
    def check_len(string_key):
        """     
        check if the length of the key is exactly four characters --
        -- and raise an exception if it isn't)
        """     
        if len(string_key) != 4:
            raise Eggog("'%s': EGI wants the key to be exactly four characters!" % string_key)     
        else:
            return True     
        
    @staticmethod     
    def try_as_int(i):
        """     
        check if the value is an integer value or compatible (say, 1.0) and transform it to an integer -- 
        may be a long one; if this is not so -- raise an exception 
        """     
        try:     
            ret = int(i)
            if ret != i: 
                raise exceptions.Exception("conversion failed")
        except:
            raise Eggog("'%s': failed to convert to a (Python) integer!" % repr(i))
        return ret


class _Format:
    """     
    a wrapper around a dictionary that contains 'struct' format strings
    for the command extentions     
    """     

    def __init__(self):
        """
        create the dictionary
        """
        self._format_strings = \
            {'Q': "=4s",
             'X': '',
             'B': '',
             'E': '',
             'A': '',
             'T': "=L", 
             'D': None,     
             'I': "=B",
             'Z': '',
             'F': "=4c"
             }

    def __getitem__(self, key):

        return self._format_strings.get(key)

    def format_length(self, key):
        """
        return the number of the bytes to read or write for the given command code
        """
        return struct.calcsize(self[key])     

    def pack(self, key, *args):
        """
        pack the arguments according to the format
        """
        fmt = '=c' + self[key].lstrip('=')     
        result = struct.pack(fmt, key, *args)     
        return result
    
    def unpack(self, key, data):
        """
        unpack the argument according to the format
        """
        return struct.unpack(self[key], data)


class _DataFormat:
    """
    a helper for creating the "Extended" events (many key fields, variable data)
    """

    def __init__(self):     
        """
        create the main reference table
        """

        self._translation_table = \
            {type(True): ('bool', '=?'),
             type(1): ('long', '=l'),
             type(1L): ('long', '=l'),
             type(1.0): ('doub', '!d'),
             type(''): ('TEXT', '%ds'),
             }
        self._check_table = \
            {type(1): is_32_bit_int_compatible,
             type(1L): is_32_bit_int_compatible,
             }

    def _get_hints(self, data):     
        """
        try to preprocess the data before getting the packing hints
        """
        hints = None
        is_ok = self._check_table.get(type(data), lambda x: True)
        if is_ok(data):
            hints = self._translation_table.get(type(data), None)
        return hints

    def _pack_data(self, data):
        """
        try to pack the argument according to its type; by default, a str() conversion is sent
        """
        hints = self._get_hints(data)
        if hints is None:
            return self._pack_data(str(data))
        desctype = hints[0]
        if desctype == 'TEXT':     
            length = len(data)
            data_str = data     
        else:
            length = struct.calcsize(hints[1])
            data_str = struct.pack(hints[1], data)
        length_str = struct.pack('=H', length)
        return _cat(desctype, length_str, data_str)
    
    def _pack_dict(self, table, pad = False):
        """
        pack the data from the given dictionary for sending ;
        if the 'pad' argument is False, the keys must be four-character strings ,
        otherwise they will be converted to strings by str() and then truncated
        or padded with spaces .
        Note that for the latter case the uniqueness of the generated key ids is not quaranteed .
        """
        keys, values = zip(*table.items())
        if len(keys) <= 0:
            return struct.pack('0s', '')     
        if not pad:
            map(Eggog.check_type, keys)     
            map(Eggog.check_len, keys)
        else:
            for i in xrange(len(keys)):
                k = keys[i]
                if isinstance(k, type('')):
                    k = make_fit(str(k))
                    keys[i] = k
        nkeys = len(keys)
        if nkeys > 255:
            raise Eggog("too many keys to send (%d > 255)" % (nkeys,))     
        nkeys_str = struct.pack('=B', nkeys)
        values_packed = map(self._pack_data, values)
        items_packed = [nkeys_str, ] * (2 * nkeys + 1)
        items_packed[1::2] = keys[:]
        items_packed[2::2] = values_packed
        result = _cat(*items_packed)
        return result

    def _make_event_header(self, size_of_the_rest, timestamp, duration, keycode):
        """
        make an event message header from the given data according to the protocol
        'size_of_the rest' is the size of the rest part of the event message
        """     
        sizeof_int32 = 4
        addendum = 3 * sizeof_int32
        total_length = addendum + size_of_the_rest
        result_str = struct.pack("=sH2L4s", 'D', total_length, timestamp, duration, keycode)
        return result_str

    def pack(self, key, timestamp = None, label = None, description = None, table = None, pad = False):     
        """     
        pack the arguments according to the Netstation Event structure ;

        if the 'pad' argument is 'False' -- an exception is raised in the case
        if either the main key or one from the table keys is not a (unique)
        four-character string ; otherwise, if the 'pad' value is True,
        the routine tries to convert truncate or pad the key to form a 4-byte string .

        nb. if the 'timestamp' argument is None -- the according field is set
            by a local routine at the moment of the call .
        """     
        duration = 1
        if timestamp is None:
            timestamp = ms_localtime()
        if not is_32_bit_int_compatible(timestamp):
            raise Eggog("only 'small' 32-bit integer values less than %d are accepted as timestamps, not %s"  %  (0xffffFFFF, timestamp))
        if label is None:
            label = ''
        if description is None:
            description = ''
        label_str = p_string(label)
        description_str = p_string(description)     
        if table is None or len(table.keys()) <= 0:
            table_str = struct.pack('B', 0)     
        else:     
            table_str = self._pack_dict(table, pad)
        size = len(label_str) + len(description_str) + len(table_str)
        header_str = self._make_event_header(size, timestamp, duration, key)
        result_str = _cat(header_str, label_str, description_str, table_str)
        return result_str
        

class Netstation:     
    """
    Provides Python interface for a connection with the Netstation via a TCP/IP socket.
    """

    def __init__(self):
        print 'init'
        self._socket = Socket()     
        self._system_spec = _get_endianness_string()
        self._fmt = _Format()
        self._data_fmt = _DataFormat()     

    def connect(self, str_address, port_no):
        """ connect to the Netstaton machine """
        print 'connect'
        self._socket.connect(str_address, port_no)

    def disconnect(self):
        """ close the connection """
        self._socket.disconnect()

    def GetServerResponse(self, b_raise = True):
        """ read the response from the socket and convert it to a True / False resulting value """
        print 'getserverResponse'
        code = self._socket.read(1)
        if code == 'Z':
            return True
        elif code == 'F': # an 'F' <error code> sequence
            error_info_length = self._fmt.format_length(code)
            error_info = self._socket.read(error_info_length)
            if b_raise:
                err_msg = "server returned an error: " + repr(self._fmt.unpack(code, error_info))
                raise Eggog(err_msg)     
            else:
                return False     
        elif code == 'I': # a version byte should follow
            version_length = self._fmt.format_length(code)
            version_info = self._socket.read(version_length)
            version = self._fmt.unpack(code, version_info)     
            self._egi_protocol_version = version
            self._egi_protocol_version = version[0]     
            return self._egi_protocol_version
        else:
            if b_raise:
                raise Eggog("unexpected character code returned from server: '%s'" % (code,))     
            else:
                return False

    def BeginSession(self):     
        """ say 'hi!' to the server """     
        print 'beginSession'
        message = self._fmt.pack('Q', self._system_spec)
        self._socket.write(message)     
        print "BS: ", message
        return self.GetServerResponse()

    def EndSession(self):
        """ say 'bye' to the server """
        self._socket.write('X')
        return self.GetServerResponse()

    def StartRecording(self):
        """ start recording to the selected (externally) file """
        print 'startRecording'
        self._socket.write('B')     
        return self.GetServerResponse()

    def StopRecording(self):
        """
        stop recording to the selected file;
        the recording can be resumed with the BeginRecording() command
        if the session is not closed yet .
        """     
        self._socket.write('E')
        return self.GetServerResponse()

    def SendAttentionCommand(self):
        """ Sends and 'Attention' command """
        print 'sendAttention'
        self._socket.write('A')
        return self.GetServerResponse()

    def SendLocalTime(self, ms_time = None):
        """ Send the local time (in ms) to Netstation; usually this happens after an 'Attention' command """     
        if ms_time is None:
            ms_time = ms_localtime()
        message = self._fmt.pack('T', ms_time)
        self._socket.write(message)
        return self.GetServerResponse()

    def sync(self, timestamp = None):
        """ a shortcut for sending the 'attention' command and the time info """
        print 'sync'
        if (self.SendAttentionCommand()) and (self.SendLocalTime(timestamp)):
            return True
        else:
            raise Eggog("sync command failed!")

    def send_event(self, key, timestamp = None, label = None, description = None, table = None, pad = False):
        """
        Send an event ; note that before sending any events a sync() has to be called
        to make the sent events effective .

        Arguments:
        -- 'id' -- a four-character identifier of the event ;
        -- 'timestamp' -- the local time when event has happened, in milliseconds ;
                          note that the "clock" used to produce the timestamp should be the same
                          as for the sync() method, and, ideally,
                          should be obtained via a call to the same function ;
                          if 'timestamp' is None, a time.time() wrapper is used .
        -- 'label' -- a string with any additional information, up to 256 characters .
        -- 'description' -- more additional information can go here (same limit applies) .
        -- 'table' -- a standart Python dictionary, where keys are 4-byte identifiers,
                      not more than 256 in total ;
                      there are no special conditions on the values,
                      but the size of every value entry in bytes should not exceed 2 ^ 16 .

        Note A: due to peculiarity of the implementation, our particular version of NetStation
                was not able to record more than 2^15 events per session .

        Note B: it is *strongly* recommended to send as less data as possible .
        """
        message = self._data_fmt.pack(key, timestamp, label, description, table, pad)
        self._socket.write(message)     
        return self.GetServerResponse()

    def SendSimpleEvent(self, markercode, timestamp = None):
        """
        send a 'simple' marker event -- i.e. an event marker without any additional information;
        nb. the marker code must be a string of exactly four characters
        """     
        if timestamp:
            current_time = timestamp
        else:
            one_day = 1000 * 60 * 60 * 24
            current_time = math.floor(time.time() * 1000) % one_day     
        default_duration = 1 # also in milliseconds
        sizeof_int32 = 4
        event_min_size = 3 * sizeof_int32
        data_string = 'D%s%s%s%s' % (
            struct.pack('h', event_min_size),
            struct.pack('l', current_time),
            struct.pack('l', default_duration),
            struct.pack('4s', markercode),
        )
        self._socket.write(data_string)
        return self.GetServerResponse()

if __name__ == "__main__":

    print __doc__
    print "\n === \n"
    # print "module dir() listing: ", __dict__.keys()
    print "module dir() listing: ", dir()


