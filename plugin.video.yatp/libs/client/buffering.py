# -*- coding: utf-8 -*-
# Module: buffering
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Buffering torrent
"""

import os
from urllib import quote
import xbmc
import xbmcgui
import json_requests as jsonrq
from libs.simpleplugin import Addon


addon = Addon()
string = addon.get_localized_string
media_url = 'http://127.0.0.1:{0}/stream/'.format(addon.server_port)
MEDIAFILES = ('.avi', '.mkv', '.mp4', '.ts', '.m2ts', '.mov')


def get_videofiles(files):
    """
    Get a sorted list of videofiles from all files in a torrent

    :param files:
    :return: the sorted list of 3-item tuples (file_index, file_name, file_size)
    """
    videofiles = []
    for file_index, file_ in enumerate(files):
        if os.path.splitext(file_[0].lower())[1] in MEDIAFILES:
            videofiles.append((file_index, os.path.basename(file_[0]), file_[1]))
    videofiles = sorted(videofiles, key=lambda i: i[1])
    return videofiles


def add_torrent(torrent):
    """
    Add torrent for downloading

    :param torrent:
    :return:
    """
    jsonrq.add_torrent(torrent)
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create(string(32015))
    progress_dialog.update(0, string(32016))
    while not (progress_dialog.iscanceled() or jsonrq.check_torrent_added()):
        xbmc.sleep(1000)
    if not progress_dialog.iscanceled():
        progress_dialog.close()
        return jsonrq.get_last_added_torrent()
    else:
        return None


def select_file(torrent_data, dialog=False):
    """
    Select a videofile from the torrent to play

    :param torrent_data:
    :param dialog: show a dialog for selecting a videofile
    :return:
    """
    videofiles = get_videofiles(torrent_data['files'])
    if videofiles:
        if len(videofiles) > 1 and dialog:
            # Show selection dialog
            index = xbmcgui.Dialog().select(string(32017), [item[1] for item in videofiles])
        elif len(videofiles) > 1 and not dialog:
            # Select the biggest file
            file_sizes = [video[2] for video in videofiles]
            max_size = max(file_sizes)
            index = file_sizes.index(max_size)
        else:
            index = 0
        if index >= 0:
            return videofiles[index][0]
        else:
            return -1
    else:
        return None


def stream_torrent(file_index, info_hash):
    """
    Stream a videofile from torrent

    :param file_index:
    :param info_hash:
    :return:
    """
    files = jsonrq.get_files(info_hash)
    if file_index not in xrange(0, len(files) + 1):
        raise IndexError('File index {0} is out of range!'.format(file_index))
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create(string(32014))
    jsonrq.buffer_file(file_index, info_hash)
    while not (progress_dialog.iscanceled() or jsonrq.check_buffering_complete()):
        torrent_info = jsonrq.get_torrent_info(info_hash)
        progress_dialog.update(jsonrq.get_buffer_percent(),
                               string(32018).format(torrent_info['total_download']),
                               string(32019).format(torrent_info['dl_speed']),
                               string(32020).format(torrent_info['num_seeds']))
        xbmc.sleep(1000)
    if not progress_dialog.iscanceled():
        progress_dialog.close()
        return media_url + quote(files[file_index][0].replace('\\', '/').encode('utf-8'))
    else:
        jsonrq.abort_buffering()
        return ''


def buffer_torrent(torrent, file_index=None):
    """
    Buffer a torrent and resolve a playable path from it

    :param torrent: str - magnet link or .torrent file URL
    :return:
    """
    torrent_data = add_torrent(torrent)
    if torrent_data is not None:
        if file_index is None or file_index == 'dialog':
            file_index = select_file(torrent_data, file_index == 'dialog')
        if file_index is None:
            jsonrq.remove_torrent(torrent_data['info_hash'], True)
            xbmcgui.Dialog().notification(addon.id, string(32022), addon.icon, 3000)
        elif file_index >= 0:
            url = stream_torrent(file_index, torrent_data['info_hash'])
            if url:
                return url
        else:
            xbmcgui.Dialog().notification(addon.id, string(32021), addon.icon, 3000)
    if not (jsonrq.check_torrent_added() and jsonrq.check_buffering_complete()):
        xbmcgui.Dialog().notification(addon.id, string(32023), addon.icon, 3000)
    return ''
