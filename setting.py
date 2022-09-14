import os
import json
import uuid
from pathlib import Path
import subprocess

SETTING_FILE_PATH = os.getenv('LOCALAPPDATA') + r'\pptx-py\video-presenter.json'

class JsonWrapper:
    def to_dict(self):
        return self.__dict__


class Adjustment(JsonWrapper):
    def __init__(self, top, bottom, left, right):
        JsonWrapper.__init__(self)
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right

    @classmethod
    def from_json(cls, data):
        return cls(data.get('top', 0), data.get('bottom', 0), data.get('left', 0), data.get('right', 0))

class PlayBack(JsonWrapper):
    def __init__(self, loop, next):
        JsonWrapper.__init__(self)
        self.loop = loop
        self.next = next

    @classmethod
    def from_json(cls, data):
        return cls(data.get('loop', 0), data.get('next', 0))


class Profile:
    current_id = ''
    profiles = []
    videos = []

    def __init__(self, **kwargs):
        for arg in kwargs:
            self.__dict__[arg] = kwargs[arg]
    
    def to_dict(self):
        return { **self.__dict__, 'adjustment': self.adjustment.to_dict(), 'playback': self.playback.to_dict() }

    @classmethod
    def from_json(cls, data = {}):
        '''all attributes of Profile instance are specified here only'''
        return cls(
            id = data.get('id', uuid.uuid4().hex),
            name = data.get('name', 'default'),
            volume = data.get('volume', 100),
            fadeout_second = data.get('fadeout_second', 0.5),
            adjustment = Adjustment.from_json(data.get('adjustment', {})),
            playback = PlayBack.from_json(data.get('playback', {})),
            skip_step = data.get('skip_step', 1)
        )


    @classmethod
    def load_all(cls):
        '''load app settings from disk'''
        if os.path.exists(SETTING_FILE_PATH):
            with open(SETTING_FILE_PATH, 'r') as file:
                try:
                    loaded = json.loads(file.read())

                    if isinstance(loaded.get('videos'), list):
                        cls.videos = [vpath for vpath in loaded['videos'] if os.path.exists(vpath)]
                    for p in loaded['profiles']:
                        cls.profiles.append(cls.from_json(p))
                except:
                    if len(cls.profiles) == 0:
                        cls.profiles.append(cls.from_json({}))
        else:
            cls.profiles.append(cls.from_json({}))

    @classmethod
    def save_all(cls):
        '''save all profiles into disk'''
        dirname = os.path.dirname(SETTING_FILE_PATH)
        Path(dirname).mkdir(parents=True, exist_ok=True)

        json_to_save = { 
            'profiles': cls.profiles_to_save(),
            'videos': cls.videos
        }
        json_to_save = json.dumps(json_to_save, indent=2)
        with open(SETTING_FILE_PATH, 'r') as f:
            json_saved = f.read()

        if json_saved != json_to_save:
            with open(SETTING_FILE_PATH, 'w') as f:
                f.write(json_to_save)

    @classmethod
    def profiles_to_save(cls):
        '''convert all profiles from object to dict (for saving to disk)'''
        return [p.to_dict() for p in cls.profiles]

    @classmethod
    def add_profile(cls, name):
        cls.profiles.append(cls.from_json({ 'name': name }))

    @classmethod
    def remove_profile(cls, id):
        profile = next((p for p in cls.profiles if p.id == id))
        if profile is not None: cls.profiles.remove(profile)

    @classmethod
    def get_profile(cls, id):
        return next((p for p in cls.profiles if p.id == id))


    @classmethod
    def get_current(cls):
        current_profile = next((p for p in cls.profiles if p.id == cls.current_id), cls.profiles[0])
        if current_profile.id != cls.current_id:
            cls.current_id = current_profile.id
        return current_profile 

    @classmethod
    def set_current(cls, id):
        cls.current_id = id


    @staticmethod
    def show_save_location():
        subprocess.Popen('explorer /select,{}'.format(SETTING_FILE_PATH))


