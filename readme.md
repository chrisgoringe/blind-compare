# Quick blind AB comparison

Compare two or more sets of images, normally generated with most things the same. For instance... same seed and prompt, different model.

## Shameless plug for my ComfyUI custom nodes

- [Use Everywhere](https://github.com/chrisgoringe/cg-use-everywhere) - eliminate spaghetti by invisible broadcasting. 
- [Image picker](https://github.com/chrisgoringe/cg-image-picker) - pause the execution and let you choose an image or images to continue with.

Love my work? [Buy me a coffee!](https://www.buymeacoffee.com/chrisgoringe)

## Organising your images

The images need to be named in such a way that a simple string match will find all images in the first set, and a substitution of that string with another will give the filename of the corresponding image in another set. 

```
made_with_model_one_00001.png
made_with_model_two_00001.png
made_with_model_three_00001.png
made_with_model_one_00002.png
made_with_model_two_00002.png
made_with_model_three_00002.png
...
made_with_model_one_00080.png
made_with_model_two_00080.png
made_with_model_three_00080.png
```

works with `--match=one` and `--sub=two,three`.

In general you want the corresponding images (so all three _00002 images, for instance) to have been generated with the same parameters except for the difference you are testing (in this example, the model used).

## Running a comparison

Rename `arguments-example.txt` as `arguments.txt`, and edit it appropriately. You need to specify the directory, match, and substitutions, the rest is optional. The run with

`python blind_ab_scorer.py @arguments.txt`

A random image from the original set will be chosen, and the corresponding images from all other sets. They will be displayed in random order. You pick your favourite, and a new set is displayed, until all images in the original set have been used (or you quit by pressing `q`). Then the stats will be displayed in the console:

```
  one chosen   6 times
  two chosen  25 times
three chosen   3 times
```

Looks like you really like `model_two`.

### Picking an image

 Choose your favourite image with the numbers on the keyboard. By default, you select by counting from 1, left to right, top to bottom, and pressing the corresponding key. For example, with four images per row:

|1|2|3|4|
|-|-|-|-|
|5|6|7|8|

## Other options

### `--keypad`

If you specify `--keypad` then you pick images using the keypad layout by pressing the keypad key corresponding to the position of the image, so (regardless of the number of images per row and number of rows):

|7|8|9|
|-|-|-|
|4|5|6|
|1|2|3|

`--keypad` cannot be used with more than 3 images per row or more than three rows. Obviously.

### `--verbose`

`--verbose` can be used to print your choices to the console (perhaps to check you understand what number to press!). I would *strongly* discourage you from using this during a run, since the whole point of a blind test is that you don't know which set you are choosing from!
