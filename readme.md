# Quick blind AB comparison

Compare two sets of images generated with most things the same. For instance... same seed and prompt, different model.

## Images

The images need to be in pairs with names which match with a simple text substitutions. You specify a string that matches the first set of images, and a substitution that, when it replaces the first string, gives the name of the second image. For instance:

```
made_with_model_one_1.png
made_with_model_two_1.png
made_with_model_one_2.png
made_with_model_two_2.png
```

works with `--match=one` and `--sub=two`.

Take `arguments-example.txt` and rename it `arguments.txt`, and edit it appropriately.

```
--directory=[directory the images are in]
--match=[string that matches first set of images]
--sub=[string that substitutes for match in the second set of images]
--height=[height of the window
```

Then `python blind_ab_scorer @arguments.txt`