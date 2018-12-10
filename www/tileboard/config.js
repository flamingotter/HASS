var CONFIG = {
  ignoreErrors: true,
  customTheme: CUSTOM_THEMES.TRANSPARENT, // CUSTOM_THEMES.TRANSPARENT, CUSTOM_THEMES.MATERIAL, CUSTOM_THEMES.MOBILE, CUSTOM_THEMES.COMPACT, CUSTOM_THEMES.HOMEKIT, CUSTOM_THEMES.WINPHONE, CUSTOM_THEMES.WIN95
  transition: TRANSITIONS.ANIMATED_GPU, //ANIMATED or SIMPLE (better perfomance)
  entitySize: ENTITY_SIZES.SMALL, //SMALL, BIG are available
  tileSize: 100,
  tileMargin: 6,
  serverUrl: "https://ha.flamingotter.com",
  wsUrl: "wss://ha.flamingotter.com/api/websocket",
  authToken: null, // optional: make an long live token and put it here
  //googleApiKey: "XXXXXXXXXX", // Required if you are using Google Maps for device tracker
  debug: false, // Prints entities and state change info to the console.

  // next fields are optional
  events: [],
  timeFormat: 24,
  menuPosition: MENU_POSITIONS.BOTTOM, // or BOTTOM
  hideScrollbar: false, // horizontal scrollbar
  groupsAlign: GROUP_ALIGNS.HORIZONTALLY, // or VERTICALLY

  header: { // https://github.com/resoai/TileBoard/wiki/Header-configuration
    styles: {
        padding: '0px 130px 100px 50px',
        fontSize: '18px'
    },
      right: [
        {
          type: HEADER_ITEMS.WEATHER,
          styles: {
            margin: '0 0 0'
          },
          state: '&sensor.dark_sky_summary.state', // label with weather summary
          icon: '&sensor.dark_sky_icon.state',
          icons: {
            'clear-day': 'clear',
            'clear-night': 'nt-clear',
            'cloudy': 'cloudy',
            'rain': 'rain',
            'sleet': 'sleet',
            'snow': 'snow',
            'wind': 'hazy',
            'fog': 'fog',
            'partly-cloudy-day': 'partlycloudy',
            'partly-cloudy-night': 'nt-partlycloudy'
          },
          fields: {
            summary: '&sensor.dark_sky_summary.state',
            temperature: '&sensor.dark_sky_temperature.state',
            temperatureUnit: '&sensor.dark_sky_temperature.attributes.unit_of_measurement',
            //feels: '&sensor.dark_sky_apparent_temperature.state'
            //feelsUnit: '&sensor.dark_sky_apparent_temperature.attributes.unit_of_measurement',
          }
        }
      ],
      left: [
        {
          type: HEADER_ITEMS.DATETIME,
          dateFormat: 'EEEE, LLLL dd', //https://docs.angularjs.org/api/ng/filter/date
        }
      ]
  },

  /*screensaver: {// optional. https://github.com/resoai/TileBoard/wiki/Screensaver-configuration
      timeout: 300, // after 5 mins of inactive
      slidesTimeout: 10, // 10s for one slide
      styles: { fontSize: '40px' },
      leftBottom: [{ type: SCREENSAVER_ITEMS.DATETIME }], // put datetime to the left-bottom of screensaver
      slides: [
         { bg: 'images/bg1.jpeg' },
         {
            bg: 'images/bg2.png',
            rightTop: [ // put text to the 2nd slide
               {
                  type: SCREENSAVER_ITEMS.CUSTOM_HTML,
                  html: 'Welcome to the <b>TileBoard</b>',
                  styles: { fontSize: '40px' }
               }
            ]
         },
         { bg: 'images/bg3.jpg' }
      ]
    },*/

    pages: [
      {
        title: 'Main page',
        bg: [],
        icon: 'mdi-home-outline', // home icon
        groups: [
          {
            title: 'Rooms',
            width: 3,
            height: 3,
            items: [
              {
                position: [2, 0],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.office', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-desktop-tower-monitor",
                  off: "mdi-desktop-tower-monitor",
                },
              },
              {
                position: [1, 0],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.living_room', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-sofa",
                  off: "mdi-sofa",
                },
              },
              {
                position: [1, 1],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.dining_room', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-silverware",
                  off: "mdi-silverware",
                },
              },
              {
                position: [1, 2],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.kitchen', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-stove",
                  off: "mdi-stove",
                },
              },
              {
                position: [0, 0],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.bedroom', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-hotel",
                  off: "mdi-hotel",
                },
              },
              {
                position: [0, 1],
                width: 1,
                type: TYPES.SWITCH,
                id: 'group.stairs', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-stairs",
                  off: "mdi-stairs",
                },
              },
            ]
          },

          {
            title: 'Status',
            width: 2,
            height: 3,
            items: [
              {
                position: [0, 0],
                width: 2,
                title: 'Home',
                //classes: ['-small-entity'],
                type: TYPES.SENSOR,
                id: 'input_select.home_status',
                state: false
              },
              {
                position: [0, 1],
                width: 1,
                title: 'Josh',
                //classes: ['-small-entity'],
                type: TYPES.INPUT_SELECT,
                id: 'input_select.josh_status',
                state: false
                //bg: 'images/josh.jpg',
              },
              {
                position: [1, 1],
                width: 1,
                title: 'MJ',
                //classes: ['-small-entity'],
                type: TYPES.INPUT_SELECT,
                id: 'input_select.mj_status',
                state: false
              }
            ]
          },
          /*{
            title: 'Weather',
            width: 1,
            height: 3,
            items: [
              {
                // please read README.md for more information
                // this is just an example
                position: [0, 0],
                height: 3, // 1 for compact
                //classes: ['-compact'],
                type: TYPES.WEATHER,
                id: {},
                state: '&sensor.dark_sky_summary.state', // label with weather summary
                icon: '&sensor.dark_sky_icon.state',
                icons: {
                  'clear-day': 'clear',
                  'clear-night': 'nt-clear',
                  'cloudy': 'cloudy',
                  'rain': 'rain',
                  'sleet': 'sleet',
                  'snow': 'snow',
                  'wind': 'hazy',
                  'fog': 'fog',
                  'partly-cloudy-day': 'partlycloudy',
                  'partly-cloudy-night': 'nt-partlycloudy'
                },
                fields: {
                  summary: '&sensor.dark_sky_summary.state',
                  temperature: '&sensor.dark_sky_temperature.state',
                  temperatureUnit: '&sensor.dark_sky_temperature.attributes.unit_of_measurement',
                  windSpeed: '&sensor.dark_sky_wind_speed.state',
                  humidity: '&sensor.dark_sky_humidity.state',
                  humidityUnit: '&sensor.dark_sky_humidity.attributes.unit_of_measurement',
                  list: [
                    'Feels like '
                      + '&sensor.dark_sky_apparent_temperature.state'
                      + '&sensor.dark_sky_apparent_temperature.attributes.unit_of_measurement',

                    'Pressure '
                      + '&sensor.dark_sky_pressure.state'
                      + '&sensor.dark_sky_pressure.attributes.unit_of_measurement',

                    '&sensor.dark_sky_precip_probability.state'
                      + '&sensor.dark_sky_precip_probability.attributes.unit_of_measurement'
                      + ' chance of rain'
                  ]
                }
              }
            ]
          }*/
        ]
      },
      {
        title: 'Living Room',
        bg: '[]',
        icon: 'mdi-sofa',
        groups: [
          {
            title: 'Lights',
            width: 1,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Lamps',
                //subtitle: 'Lounge',
                id: 'group.living_room_lamps',
                type: TYPES.SWITCH,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
			  },
			  {
                position: [0, 1],
                title: 'Corner Lamp',
                //subtitle: 'Lounge',
                id: 'light.corner_lamp',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
			  {
                position: [1, 1],
                title: 'Table Lamp',
                //subtitle: 'Lounge',
                id: 'light.table_lamp',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
              {
                position: [0, 2],
                title: 'Paper Lamp',
                //subtitle: 'Lounge',
                id: 'switch.paper_lamp',
                type: TYPES.SWITCH,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
              },
			  {
                position: [1, 2],
                title: 'Spot Light',
                //subtitle: 'Lounge',
                id: 'light.spot_light',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  { 
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
            ]
          },
        ]
      },
	  {
        title: 'Kitchen',
        bg: '[]',
        icon: 'mdi-stove',
        groups: [
          {
            title: 'Lights',
            width: 1,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'kitchen Light',
                //subtitle: 'Lounge',
                id: 'light.kitchen_light',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
              {
                position: [0, 1],
                title: 'Cabinet Light',
                //subtitle: 'Lounge',
                id: 'switch.cabinet_light',
                type: TYPES.SWITCH,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
              },
            ]
          },
        ]
      },
	  {
        title: 'Dining Room',
        bg: '[]',
        icon: 'mdi-silverware',
        groups: [
          {
            title: 'Lights',
            width: 1,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Dining Light',
                //subtitle: 'Lounge',
                id: 'light.dining_light',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
              {
                position: [0, 1],
                title: 'Dinner Table',
                //subtitle: 'Lounge',
                id: 'light.dinner_light',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
				]
              },
            ]
          },
        ]
      },
      {
        title: 'Master Bedroom',
        bg: '[]',
        icon: 'mdi-hotel',
        groups: [
          {
            title: 'Lights',
            width: 2,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Eugene',
                //subtitle: 'Lounge',
                id: 'light.eugene',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
                  /*{
                    title: 'Color temp',
                    field: 'color_temp',
                    max: 588,
                    min: 153,
                    step: 15,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "color_temp"
                    }
                  }*/
                ]
              },
              {
                position: [0, 1],
                title: 'Under Bed',
                //subtitle: 'Lounge',
                id: 'light.under_bed',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness"
                    }
                  },
                ]
              },
              {
                position: [1, 0],
                title: 'Rapunzel',
                //subtitle: 'Lounge',
                id: 'light.rapunzel',
                type: TYPES.LIGHT,
                state: false,
                states: {
                  on: "On",
                  off: "Off"
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
                sliders: [
                  {
                    title: 'Brightness',
                    field: 'brightness',
                    max: 255,
                    min: 0,
                    step: 5,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "brightness",
                    }
                  },
                  /*{
                    title: 'Color temp',
                    field: 'color_temp',
                    max: 588,
                    min: 153,
                    step: 15,
                    request: {
                      type: "call_service",
                      domain: "light",
                      service: "turn_on",
                      field: "color_temp"
                    }
                  }*/
                ]
              },
            ]
          },
          {
            title: 'Misc',
            width: 2,
            height: 3,
            items: [
              {
                position: [0, 0],
                title: 'Bedroom Fan',
                width: 1,
                type: TYPES.SWITCH,
                id: 'switch.bed_fan', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                    off: "Off",
                },
                icons: {
                  on: "mdi-fan",
                  off: "mdi-fan-off",
                },
              },
            ]
          },
          {
            title: 'Sleep',
            width: 1,
            height: 3,
            items: [
              {
                position: [0, 0],
                title: 'Josh Sleep',
                width: 1,
                type: TYPES.SWITCH,
                id: 'input_boolean.ib_j_status_sleeping',
                state: false,
                states: {
                  on: "On",
                  off: "Off",
              },
                icons: {
                  on: "mdi-sleep",
                  off: "mdi-sleep-off",
                },
              },
              {
                position: [0, 1],
                title: 'MJ Sleep',
                width: 1,
                type: TYPES.SWITCH,
                id: 'input_boolean.ib_m_status_sleeping',
                state: false,
                states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-sleep",
                  off: "mdi-sleep-off",
                },
              },
            ]
          },
        ]
      },
	  {
        title: 'Office page',
        bg: '[]',
        icon: 'mdi-desktop-tower-monitor',
        groups: [
          {
            title: 'Lights',
            width: 1,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Desk Light',
                //subtitle: 'Lounge',
                id: 'switch.desk_light',
                type: TYPES.SWITCH,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
              },
              {
                position: [0, 1],
                title: 'Office Light',
                //subtitle: 'Lounge',
                id: 'switch.office_light',
                type: TYPES.SWITCH,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-lightbulb-on",
                  off: "mdi-lightbulb",
                },
              },
            ]
          },
          {
            title: 'Misc',
            width: 1,
            height: 3,
            items: [
              {
                position: [0, 0],
                title: 'Office Fan',
                width: 1,
                type: TYPES.SWITCH,
                id: 'switch.office_fan', // using empty object for an unknown id
                state: false,
                states: {
                  on: "On",
                    off: "Off",
                },
                icons: {
                  on: "mdi-fan",
                  off: "mdi-fan-off",
                },
              },
              {
                position: [0, 1],
                title: '3D Saftey',
                width: 1,
                type: TYPES.SWITCH,
                id: 'input_boolean.3dprinter_saftey',
                state: false,
				states: {
                  on: "On",
                    off: "Off",
                },
                icons: {
                  on: "mdi-lock-open",
                  off: "mdi-lock",
                },
              },
              {
                position: [0, 2],
                title: '3D Power',
                width: 1,
                type: TYPES.SWITCH,
                id: 'input_boolean.3dprinter_power',
                state: false,
				states: {
                  on: "On",
                    off: "Off",
                },
                icons: {
                  on: "mdi-power-plug",
                  off: "mdi-power-plug-off",
                },
              },
              /*{
                position: [0, 2],
                id: 'camera.octoprint',
                type: TYPES.CAMERA_THUMBNAIL,
                bgSize: 'cover',
                width: 1,
                state: false,
                fullscreen: {
                    type: TYPES.CAMERA,
                    refresh: 500, // can be number in milliseconds
                    bgSize: 'contain'
                },
                refresh: function () { // can also be a function
                    return 3000 + Math.random() * 1000
                }
              }*/
            ]
          },
          {
            title: 'Enviroment',
            width: 2,
            height: 3,
            items: [
              {
                position: [0, 0],
                title: 'Motion',
                width: 1,
                type: TYPES.SENSOR_ICON,
                id: 'sensor.motion_test', // using empty object for an unknown id
                state: false,
                states: {
                  detected: "Detected",
                  standby: 'Standby',
                },
                icons: {
                  detected: "mdi-run-fast",
                  standby: "mdi-run",
                },
              },
              {
                position: [0, 1],
                title: 'Temp',
                width: 1,
                type: TYPES.SENSOR,
                id: 'sensor.test_temp', // using empty object for an unknown id
                state: false,
                filter: function (value) { // optional
                  var num = parseFloat(value);
                  return num && !isNaN(num) ? num.toFixed(1) : value;
                }
              },
              {
                position: [1, 1],
                title: 'Hum',
                width: 1,
                type: TYPES.SENSOR,
                id: 'sensor.test_hum', // using empty object for an unknown id
                state: false,
                filter: function (value) { // optional
                  var num = parseFloat(value);
                  return num && !isNaN(num) ? num.toFixed(1) : value;
                }
              },
              {
                position: [1, 0],
                title: 'Lux',
                width: 1,
                type: TYPES.SENSOR,
                id: 'sensor.test_lux', // using empty object for an unknown id
                state: false,
                filter: function (value) { // optional
                  var num = parseFloat(value);
                  return num && !isNaN(num) ? num.toFixed(1) : value;
                }
              },
            ]
          },
        ]
      },
      
      {
         title: 'Weather',
         icon: 'mdi-weather-partlycloudy',
         groups: [
            {
               // title: 'Weather',
               width: 9,
               height: 3,
               items: [
                  {
                     position: [0, 0],
                     width: 9,
                     height: 1,
                     title: 'Forecast Summary',
                     id: {}, // since we are binding each list item to different sensor, so we simply use an empty object
                     type: TYPES.TEXT_LIST,
                     state: false,
                     list: [
                        {
                           title: '&sensor.dark_sky_hourly_summary.state'
                        },
                        {
                           title: '&sensor.dark_sky_daily_summary.state'
                        },
                     ]
                  },
                  /*{
                     position: [2, 1],
                     id: 'camera.rainradar',
                     type: TYPES.CAMERA_THUMBNAIL,
                     bgSize: 'cover',
                     width: 3,
                     height: 3,
                     state: false,
                     fullscreen: {
                        type: TYPES.CAMERA,
                        refresh: 1500, // can be number in milliseconds
                        bgSize: 'contain'
                     },
                     refresh: function () { // can also be a function
                        return 3000 + Math.random() * 1000
                     }
                  },
                  {
                     position: [5, 1],
                     id: 'camera.sydney',
                     type: TYPES.CAMERA_THUMBNAIL,
                     bgSize: 'cover',
                     width: 3,
                     height: 3,
                     state: false,
                     fullscreen: {
                        type: TYPES.CAMERA,
                        refresh: 1500, // can be number in milliseconds
                        bgSize: 'contain'
                     },
                     refresh: function () { // can also be a function
                        return 3000 + Math.random() * 1000
                     }
                  },*/
                  {
                     position: [0, 1],
                     type: TYPES.WEATHER_LIST,
                     width: 3,
                     height: 3,
                     title: 'Forecast',
                     id: {},
                     icons: {
                        'clear-day': 'clear',
                        'clear-night': 'nt-clear',
                        'cloudy': 'cloudy',
                        'rain': 'rain',
                        'sleet': 'sleet',
                        'snow': 'snow',
                        'wind': 'hazy',
                        'fog': 'fog',
                        'partly-cloudy-day': 'partlycloudy',
                        'partly-cloudy-night': 'nt-partlycloudy'
                     },
                     hideHeader: false,
                     secondaryTitle: 'Rain',
                     list: [1,2,3,4,5,6,7].map(function (id) {
                        var d = new Date(Date.now() + id * 24 * 60 * 60 * 1000);
                        var date = d.toString().split(' ').slice(1,3).join(' ');
                        var forecast = "&sensor.dark_sky_daytime_high_temperature_" + id + ".state - ";
                        forecast += "&sensor.dark_sky_overnight_low_temperature_" + id + ".state";
                        forecast += "&sensor.dark_sky_daytime_high_temperature_" + id + ".attributes.unit_of_measurement";
                        var rain = "&sensor.dark_sky_precip_probability_" + id + ".state";
                        rain += " &sensor.dark_sky_precip_probability_" + id + ".attributes.unit_of_measurement";
                        return {
                           date: date,
                           icon: "&sensor.dark_sky_icon_" + id + ".state",
                           //iconImage: null, replace icon with image
                           primary: forecast,
                           secondary: rain
                        }
                     })
                  },
               ]
            },
         ]
      },
      
	  {
        title: 'Settings',
        bg: '[]',
        icon: 'mdi-wrench',
        groups: [
          {
            title: 'On/Off',
            width: 2,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Cleaning',
                //subtitle: 'Lounge',
                id: 'input_boolean.cleaning',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-broom",
                  off: "mdi-broom",
                },
              },
              {
                position: [1, 0],
                title: 'House Guests',
                //subtitle: 'Lounge',
                id: 'input_boolean.guests_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-account-multiple-plus",
                  off: "mdi-account-multiple-plus",
                },
              },
			  {
                position: [0, 1],
                title: 'Pets Home',
                //subtitle: 'Lounge',
                id: 'input_boolean.pet_presence_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-paw",
                  off: "mdi-paw",
                },
              },
			  {
                position: [1, 1],
                title: 'Media Actions',
                //subtitle: 'Lounge',
                id: 'input_boolean.media_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-television",
                  off: "mdi-television",
                },
              },
            ]
          },
        ]
      },
	  {
        title: 'Garage',
        bg: '[]',
        icon: 'mdi-garage',
        groups: [
          {
            title: 'Items',
            width: 2,
            height: 3,
            items:
            [
              {
                position: [0, 0],
                title: 'Cleaning',
                //subtitle: 'Lounge',
                id: 'input_boolean.cleaning',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-broom",
                  off: "mdi-broom",
                },
              },
              {
                position: [1, 0],
                title: 'House Guests',
                //subtitle: 'Lounge',
                id: 'input_boolean.guests_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-account-multiple-plus",
                  off: "mdi-account-multiple-plus",
                },
              },
			  {
                position: [0, 1],
                title: 'Pets Home',
                //subtitle: 'Lounge',
                id: 'input_boolean.pet_presence_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-paw",
                  off: "mdi-paw",
                },
              },
			  {
                position: [1, 1],
                title: 'Media Actions',
                //subtitle: 'Lounge',
                id: 'input_boolean.media_lockout',
                type: TYPES.INPUT_BOOLEAN,
                state: false,
				states: {
                  on: "On",
                  off: "Off",
                },
                icons: {
                  on: "mdi-television",
                  off: "mdi-television",
                },
              },
            ]
          },
        ]
      },
    ],
  }
