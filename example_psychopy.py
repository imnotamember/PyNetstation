#!/usr/bin/env python2

# >>> import and initialization >>>
from psychopy import visual, core, event

# # This will import the debugging version of the PyNetStation module,
# #  which will not actually attempt a connection but will check to make sure
# #  your code is properly functioning.
import egi.fake as egi  # FOR TESTING WITHOUT CONNECTION TO NETSTATION COMPUTER

# # This will import the single-threaded version of the PyNetStation module
# import egi.simple as egi # FOR RUNNING CONNECTED TO NETSTATION COMPUTER -- USE THIS IN A REAL EXPERIMENT

# create stim window
myWin = visual.Window((800.0, 800.0), allowGUI=False, winType='pyglet',
                      monitor='testMonitor', units='deg', screen=0)
myWin.recordFrameIntervals = True
sans = ['Gill Sans MT', 'Arial', 'Helvetica', 'Verdana']  # use the first font found on this list

# # Create a proper timing object to reference. To retrieve the time you want later,
# #  call this method using ms_localtime(), it returns the time in a millisecond format
# #  appropriate for the NetStation TCP/IP protocol.
# # This is only necessary if you are in need of direct contact with the clock object that NetStation is utilizing,
# #  which you don't actually need since it's working behind the scenes in the egi module.
# ms_localtime = egi.ms_localtime

# # Create the NetStation event-sending object. After this you can call
# #  the methods via the object instance, in this case 'ns'.
ns = egi.Netstation()

# # The next line is for connecting the actual, single-threaded module version to the computer.
ns.connect('11.0.0.42', 55513)  # sample address and port -- change according to your network settings ---SIMPLE---

# # This sends some initialization info to NetStation for recording events.
ns.BeginSession()
# # This synchronizes the clocks of the stim computer and the NetStation computer.
ns.sync()

# # This starts the recording in NetStation acquisition. Equivalent to pressing the Record button.
# # If at some point you pause the experiment using the "StopRecording()" method,
# #  just call this method again to restart the recording.
ns.StartRecording()

fpsText = visual.TextStim(myWin,
                          units='norm', height=0.1,
                          pos=(-0.98, -0.98), text='starting...',
                          font=sans,
                          alignHoriz='left', alignVert='bottom',
                          color='BlanchedAlmond')
directionsText = visual.TextStim(myWin,
                                 units='norm', height=0.1,
                                 pos=(0, 0), text='Press Q to quit. Watch the Output for sent messages.',
                                 font=sans,
                                 alignHoriz='left', alignVert='bottom',
                                 color='BlanchedAlmond')

trialClock = core.Clock()
t = 0
lastFPSupdate = 0

# # Continues the loop until one of these keys are pressed
while not event.getKeys(keyList=['escape', 'q']):
    # # This re-aligns the clocks between the stim computer and the NetStation computer.
    # # Best to put at the start of each trial for maximal timing accuracy.
    ns.sync()

    inner_loop = True
    while inner_loop:  # Our "trial" loop.
        t = trialClock.getTime()

        if t - lastFPSupdate > 1:  # update the fps every second
            fps_value = myWin.fps()
            fpsText.text = "%i fps" % fps_value
            lastFPSupdate += 1
            # # This line takes a variable amount of arguments, but I find it best practice to define
            # #  each variable and value so as to avoid unexpected results in the events.
            # # See the end of this file for detailed description of each field.
            # # Make sure to use 'timestamp=None' as this will default to capturing timestamp when event is being sent.
            # # To make sure this is working properly, check the event info in NetStation (or the console if you're
            # #  using the egi.fake module) and make sure 'evt_' is occurring every 1000ms (or 1 second, specified in
            # #  the "if" statement above).
            # # When sending events, if you want events to be paired to your screen flip (typically the case) then place
            # #  the function call "ns.send_event()" within your window's "callOnFlip()" function. To do this, just
            # #  replace "myWin" with your psychopy created window's instance name and edit the following parameters to
            # #  suit your needs. I've attached the documentation for this function at the bottom of this script.
            myWin.callOnFlip(ns.send_event, key='evt_', timestamp=None, label="event", description="More Info",
                             table={'fld1': 123, 'fld2': "abc", 'fld3': 0.042, 'FPS_': fps_value}, pad=False)
            inner_loop = False

    fpsText.draw()  # draw fps text to screen
    directionsText.draw()  # draw directions text to screen
    myWin.flip()  # flip the window, which will lead to sending an event to NetStation
    core.wait(.05)  # wait 50ms before restarting the loop.

# # >>> we have sent all we wanted, time to go home >>>
# # This method is misleading, as it merely pauses the recording in NetStation. Equivalent to the pause button.
# # It is not actually stopping the recording session. That is done by the 'EndSession()' method below.
ns.StopRecording()

# # I don't typically use this, as it is closes the current "Session" in NetStation.
# # I find it easier to just pause the recording using "StopRecording()" and then
# # get ending impedance measurements before manually closing NetStation.
# ns.EndSession()

# # This line ends the connection via the ns object, and should then be destroying the object itself.
# # It is good practice to use so as not to waste memory or leave TCP/IP links open, which could lead to being
# # unable to reconnect without restarting the computer running the experiment.
ns.disconnect()

""" This documentation is take directly from the code file "simple.py" Remember to leave "timestamp=None" so it
 defaults to creating a timestamp when the function is called. 
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

-- 'description' -- more additional information can go here ( same limit applies ) .

-- 'table' -- a standart Python dictionary, where keys are 4-byte identifiers,
              not more than 256 in total ;
              there are no special conditions on the values,
              but the size of every value entry in bytes should not exceed 2 ^ 16 .


Note A: due to peculiarity of the implementation, our particular version of NetStation
        was not able to record more than 2^15 events per session .


Note B: it is *strongly* recommended to send as less data as possible .

"""
