import pyglet
from pyglet_gui.theme import Theme

thome = Theme({"font": "Lucida Grande",
               "font_size": 12,
               "text_color": [211, 213, 215, 255],
               "gui_color": [0, 0, 255, 255],
               "button": {
                  "down": {
                     "image": {
                        "source": "button-down.png",
                        "frame": [8, 6, 2, 2],
                        "padding": [18, 18, 8, 6]
                     },
                     "text_color": [0, 0, 0, 255]
                  },
                  "up": {
                     "image": {
                        "source": "button.png",
                        "frame": [6, 5, 6, 3],
                        "padding": [18, 18, 8, 6]
                     }
                  }
               }},
               resources_path='theme/')
taway = Theme({"font": "Lucida Grande",
               "font_size": 12,
               "text_color": [211, 213, 215, 255],
               "gui_color": [255, 0, 0, 255],
               "button": {
                  "down": {
                     "image": {
                        "source": "button-down.png",
                        "frame": [8, 6, 2, 2],
                        "padding": [18, 18, 8, 6]
                     },
                     "text_color": [0, 0, 0, 255]
                  },
                  "up": {
                     "image": {
                        "source": "button.png",
                        "frame": [6, 5, 6, 3],
                        "padding": [18, 18, 8, 6]
                     }
                  }
               }},
               resources_path='theme/')