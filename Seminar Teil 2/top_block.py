#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: LIME TRX
# Author: OE1KBC
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import analog
from gnuradio import audio
from gnuradio import blocks
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy
import sip



class top_block(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "LIME TRX", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("LIME TRX")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "top_block")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.volume = volume = 0.5
        self.samp_rate = samp_rate = 8000
        self.rf_gain = rf_gain = 30
        self.quad_rate = quad_rate = 32000
        self.ptt = ptt = 0
        self.out_rate = out_rate = 1000000
        self.freq = freq = 434550000
        self.enable_tone = enable_tone = 1

        ##################################################
        # Blocks
        ##################################################

        self._volume_range = qtgui.Range(0, 2, 0.1, 0.5, 20)
        self._volume_win = qtgui.RangeWidget(self._volume_range, self.set_volume, "Audio Gain", "dial", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._volume_win)
        self._rf_gain_range = qtgui.Range(0, 40, 1, 30, 20)
        self._rf_gain_win = qtgui.RangeWidget(self._rf_gain_range, self.set_rf_gain, "RF gain", "eng_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rf_gain_win)
        self._ptt_choices = {'Pressed': 1, 'Released': 0}

        _ptt_toggle_button = qtgui.ToggleButton(self.set_ptt, 'PTT ON/OFF', self._ptt_choices, False, 'value')
        _ptt_toggle_button.setColors("default", "default", "default", "default")
        self.ptt = _ptt_toggle_button

        self.top_layout.addWidget(_ptt_toggle_button)
        self._freq_range = qtgui.Range(434000000, 436000000, 12500, 434550000, 20)
        self._freq_win = qtgui.RangeWidget(self._freq_range, self.set_freq, "TX Frequenz", "eng_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_win)
        # Create the options list
        self._enable_tone_options = [0, 1]
        # Create the labels list
        self._enable_tone_labels = ['Send 1750Hz Tone', 'Send with Mic']
        # Create the combo box
        # Create the radio buttons
        self._enable_tone_group_box = Qt.QGroupBox("TONE/MIC Chooser" + ": ")
        self._enable_tone_box = Qt.QHBoxLayout()
        class variable_chooser_button_group(Qt.QButtonGroup):
            def __init__(self, parent=None):
                Qt.QButtonGroup.__init__(self, parent)
            @pyqtSlot(int)
            def updateButtonChecked(self, button_id):
                self.button(button_id).setChecked(True)
        self._enable_tone_button_group = variable_chooser_button_group()
        self._enable_tone_group_box.setLayout(self._enable_tone_box)
        for i, _label in enumerate(self._enable_tone_labels):
            radio_button = Qt.QRadioButton(_label)
            self._enable_tone_box.addWidget(radio_button)
            self._enable_tone_button_group.addButton(radio_button, i)
        self._enable_tone_callback = lambda i: Qt.QMetaObject.invokeMethod(self._enable_tone_button_group, "updateButtonChecked", Qt.Q_ARG("int", self._enable_tone_options.index(i)))
        self._enable_tone_callback(self.enable_tone)
        self._enable_tone_button_group.buttonClicked[int].connect(
            lambda i: self.set_enable_tone(self._enable_tone_options[i]))
        self.top_layout.addWidget(self._enable_tone_group_box)
        self.soapy_limesdr_sink_0 = None
        dev = 'driver=lime'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_limesdr_sink_0 = soapy.sink(dev, "fc32", 1, 'driver=lime,soapy=0',
                                  stream_args, tune_args, settings)
        self.soapy_limesdr_sink_0.set_sample_rate(0, 1000000)
        self.soapy_limesdr_sink_0.set_bandwidth(0, 2000000)
        self.soapy_limesdr_sink_0.set_frequency(0, freq)
        self.soapy_limesdr_sink_0.set_frequency_correction(0, 0)
        self.soapy_limesdr_sink_0.set_gain(0, min(max(rf_gain, -12.0), 64.0))
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=1000000,
                decimation=32000,
                taps=[],
                fractional_bw=0)
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_c(
            1024, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq, #fc
            250000, #bw
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        self.qtgui_waterfall_sink_x_0.enable_axis_labels(True)



        labels = ['', '', '', '', '',
                  '', '', '', '', '']
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])

        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)

        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.qwidget(), Qt.QWidget)

        self.top_layout.addWidget(self._qtgui_waterfall_sink_x_0_win)
        self.qtgui_freq_sink_x_0_0 = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq, #fc
            2000000, #bw
            'NBFM Signal', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0_0.set_y_label('Relative Gain', 'dBm')
        self.qtgui_freq_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0_0.enable_grid(True)
        self.qtgui_freq_sink_x_0_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0_0.set_fft_window_normalized(False)



        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_0_0_win, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.low_pass_filter_0 = filter.fir_filter_fff(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                4000,
                500,
                window.WIN_HAMMING,
                6.76))
        self.blocks_multiply_const_vxx_0_1 = blocks.multiply_const_cc(ptt)
        self.blocks_multiply_const_vxx_0_1.set_block_alias("ptt")
        self.blocks_multiply_const_vxx_0_0_0 = blocks.multiply_const_ff(volume)
        self.blocks_multiply_const_vxx_0_0 = blocks.multiply_const_ff(enable_tone)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(not enable_tone)
        self.blocks_add_xx_0 = blocks.add_vff(1)
        self.audio_source_0 = audio.source(samp_rate, 'Mikrofon', True)
        self.analog_sig_source_x_0 = analog.sig_source_f(8000.0, analog.GR_COS_WAVE, 1750, 0.1, 0, 0)
        self.analog_nbfm_tx_0 = analog.nbfm_tx(
        	audio_rate=8000,
        	quad_rate=32000,
        	tau=(75e-6),
        	max_dev=5e3,
        	fh=(-1.0),
                )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_nbfm_tx_0, 0), (self.blocks_multiply_const_vxx_0_1, 0))
        self.connect((self.analog_sig_source_x_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.audio_source_0, 0), (self.blocks_multiply_const_vxx_0_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_multiply_const_vxx_0_0_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_multiply_const_vxx_0_0_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0_1, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_nbfm_tx_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.qtgui_waterfall_sink_x_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.soapy_limesdr_sink_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_volume(self):
        return self.volume

    def set_volume(self, volume):
        self.volume = volume
        self.blocks_multiply_const_vxx_0_0_0.set_k(self.volume)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 4000, 500, window.WIN_HAMMING, 6.76))

    def get_rf_gain(self):
        return self.rf_gain

    def set_rf_gain(self, rf_gain):
        self.rf_gain = rf_gain
        self.soapy_limesdr_sink_0.set_gain(0, min(max(self.rf_gain, -12.0), 64.0))

    def get_quad_rate(self):
        return self.quad_rate

    def set_quad_rate(self, quad_rate):
        self.quad_rate = quad_rate

    def get_ptt(self):
        return self.ptt

    def set_ptt(self, ptt):
        self.ptt = ptt
        self.blocks_multiply_const_vxx_0_1.set_k(self.ptt)

    def get_out_rate(self):
        return self.out_rate

    def set_out_rate(self, out_rate):
        self.out_rate = out_rate

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.qtgui_freq_sink_x_0_0.set_frequency_range(self.freq, 2000000)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.freq, 250000)
        self.soapy_limesdr_sink_0.set_frequency(0, self.freq)

    def get_enable_tone(self):
        return self.enable_tone

    def set_enable_tone(self, enable_tone):
        self.enable_tone = enable_tone
        self._enable_tone_callback(self.enable_tone)
        self.blocks_multiply_const_vxx_0.set_k(not self.enable_tone)
        self.blocks_multiply_const_vxx_0_0.set_k(self.enable_tone)




def main(top_block_cls=top_block, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
