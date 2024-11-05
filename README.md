# 🚴‍♂️ pretty-gpx 🏞️

# Description

Transform your cycling or hiking adventures into stunning, ready-to-print posters with this app! Designed specifically for mountain routes, it takes your GPX file and effortlessly generates a custom poster that beautifully showcases your journey. Built on the powerful [NiceGUI](https://nicegui.io/) framework, the app offers an intuitive web interface that makes the entire process seamless.


# Demo

Here's a demo GIF to give you a glimpse of a user interacting with the webapp and exploring its features.

![](./doc/demo.gif)

# Installation

### Option 1: Install Locally

Make sure you have Python version 3.11 or higher installed.

Install the dependencies.
```
pip3 install -r .devcontainer/requirements
```

In ubuntu, install the packages.
```
sudo xargs -a .devcontainer/packages.txt apt-get install -y
```


### Option 2: Open in VS Code with Dev Containers

If you are using Visual Studio Code, you can take advantage of the Dev Containers feature:
* Install the Remote - Containers extension in VS Code.
* Open this project folder in VS Code.
* When prompted, select Reopen in Container.

This will open the project in a fully configured container environment based on the `.devcontainer` configuration, allowing you to work without manually setting up dependencies.

### Run

Finally, run the webapp.
```
python3 pretty_gpx/main.py
```


# Features

This app is the perfect companion for cycling or hiking enthusiasts tackling routes with significant elevation gain.

### 🌄 Hillshading

Add depth and realism to your map with hillshading effects that emphasize the natural ruggedness of mountainous landscapes. Adjust the sun's orientation to create the perfect lighting.

This feature leverages terrain elevation data from the [Global Copernicus Digital Elevation Model at 30 meter resolution](https://registry.opendata.aws/copernicus-dem/), ensuring high-quality elevation details for accurate and visually striking results.

### 🏔️ Mountain Passes & Elevation Profile

Easily spot mountain passes and saddles along your track, with accurate elevation information. The elevation profile, displayed below the track, mirrors these key landmarks with matching icons, giving you a clear and intuitive overview of your journey's vertical challenges.

This feature utilizes [OpenStreetMap data](https://www.openstreetmap.org) via the [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API) for precise and up-to-date information.


### 🏕️ Multi-Day Trip Support

Planning a multi-day adventure? Upload all your consecutive daily GPX tracks in one go — just ensure the filenames are in alphabetical order. The app will automatically identify and display known huts or campsites at each stop between the tracks.

### 🎨 Customization Options

Personalize your poster with options to update the track title, adjust sun orientation, and select from various color themes, making the map truly your own.

### 📥 Easy Download

Once you’ve fine-tuned your poster, simply hit the Download button to save your customized map.


### 📝 Text annotations

Placing text annotations for mountain passes, huts, or other landmarks can be challenging, as they may overlap with each other or obscure the GPX track. To ensure precise placement and a clean layout, we rely on [textalloc](https://github.com/ckjellson/textalloc), a robust tool that automatically optimizes text to prevent overlap.


### ⛶ Poster Size

When you change the poster size, the corresponding latitude and longitude area also changes. This requires a fresh request for new elevation data, as the previous data no longer covers the updated area. 

In addition to the elevation data, resizing the poster also impacts the available space around your track. This change in layout may affect the positioning of text annotations such as labels for mountain passes or huts.

Because resizing involves both requesting new elevation data and reoptimizing the text annotations, the process takes longer than simpler adjustments like changing the color theme.


# Explore new color themes

The project currently offers 4 dark and 4 light color themes, but you are encouraged to create and experiment with new ones!

In dark mode, hillshading modulates the background between black and the theme's background color. To achieve visually appealing results, the darkest color in your triplet should be assigned as the background. Ideally, it should be dark enough to maintain the readability of overlaid elements, yet distinct enough from pure black to enhance the hillshading effect.

In light mode, the approach is similar but uses white as the base, with the lightest color taking the role of the background.

The script below takes a list of color triplets as input and generates posters for both light and dark modes, helping you identify aesthetic themes. The background color is automatically selected based on brightness, while the other two colors are permuted, resulting in 4 unique posters per color triplet.

```
python3 pretty_gpx/explore_color_themes.py
```


# Simplify a GPX file

If your GPX file is quite heavy, e.g. 20Mo, you can run the following script to make it lighter.

```
python3 pretty_gpx/simplify_gpx.py --input <GPX_FILE>
```

# Examples

To give you a better idea of what this app can create, here are some example posters generated from real GPX tracks (See the `examples` folder).



<table>
  <tr>
    <td><img src="doc/posters/marmotte.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/posters/diagonale-des-fous.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
  <tr>
    <td><img src="doc/posters/hawaii.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/posters/couillole.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
  <tr>
    <td><img src="doc/posters/peyresourde.svg" style="max-width: 100%; height: auto;"/></td>
    <td><img src="doc/posters/vanoise_3days.svg" style="max-width: 100%; height: auto;"/></td>
  </tr>
</table>






# Contributing

Contributions are welcome!

When creating a Pull Request (PR), please prefix your PR title with one of the following tags to automatically apply the appropriate label:

- **feat**: Introduce a new feature
- **fix**: Fix a bug or issue
- **docs**: Improve or add documentation
- **test**: Add or modify tests
- **ci**: Update continuous integration/configuration
- **refactor**: Refactor code without changing functionality
- **perf**: Improve performance
- **revert**: Revert a previous change

### Example PR Titles:
- `feat: Add wonderful new feature`
- `fix: Correct image aspect ratio issue`

Thank you for contributing!

# License

This project is licensed under the non-commercial [CC BY-NC-SA 4.0 License](LICENSE).


