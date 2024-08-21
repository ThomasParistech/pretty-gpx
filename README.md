# 🚴‍♂️ pretty-gpx 🏞️

# Description

Transform your cycling or hiking adventures into stunning, ready-to-print posters with this app! Designed specifically for mountain routes, it takes your GPX file and effortlessly generates a custom poster that beautifully showcases your journey. Built on the powerful [NiceGUI](https://nicegui.io/) framework, the app offers an intuitive web interface that makes the entire process seamless.

# Usage

Install the dependencies.
```
pip3 install -r .devcontainer/requirements
```

And run the webapp.
```
python3 pretty_gpx/main.py
```


# Features

This app is the perfect companion for cycling or hiking enthusiasts tackling routes with significant elevation gain.

### 🌄 Hillshading

Enhance your map with a beautiful hillshaded background that highlights the ruggedness of mountainous terrains. Adjust the sun's orientation to create the perfect lighting effect.

### 🏔️ Mountain Passes & Elevation Profile

Easily spot mountain passes and saddles along your track, with accurate elevation information. The elevation profile, displayed below the track, mirrors these key landmarks with matching icons, giving you a clear and intuitive overview of your journey's vertical challenges.

### 🏕️ Multi-Day Trip Support

Planning a multi-day adventure? Upload all your consecutive daily GPX tracks in one go — just ensure the filenames are in alphabetical order. The app will automatically identify and display known huts or campsites at each stop between the tracks.

### 🎨 Customization Options

Personalize your poster with options to update the track title, adjust sun orientation, and select from various color themes, making the map truly your own.

### 📥 Easy Download

Once you’ve fine-tuned your poster, simply hit the Download button to save your customized map.




# Explore new color themes

The project currently offers 4 dark and 4 light color themes, but you are encouraged to create and experiment with new ones!

In dark mode, hillshading modulates the background between black and the theme's background color. To achieve visually appealing results, the darkest color in your triplet should be assigned as the background. Ideally, it should be dark enough to maintain the readability of overlaid elements, yet distinct enough from pure black to enhance the hillshading effect.

In light mode, the approach is similar but uses white as the base, with the lightest color taking the role of the background.

The script below takes a list of color triplets as input and generates posters for both light and dark modes, helping you identify aesthetic themes. The background color is automatically selected based on brightness, while the other two colors are permuted, resulting in 4 unique posters per color triplet.

```
python3 pretty_gpx/explore_color_themes.py
```

# Examples

To give you a better idea of what this app can create, here are some example posters generated from real GPX tracks (See the `examples` folder).




<table>
  <tr>
    <td><img src="doc/marmotte.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/diagonale-des-fous.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
  <tr>
    <td><img src="doc/hawaii.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/couillole.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
  <tr>
    <td><img src="doc/peyresourde.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/vanoise_3days.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
</table>






# Contributing

Contributions are welcome!

# License

This project is licensed under the non-commercial [CC BY-NC-SA 4.0 License](LICENSE).


