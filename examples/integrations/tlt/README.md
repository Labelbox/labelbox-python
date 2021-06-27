# NVIDIA + Labelbox

##### Turn any Labelbox bounding box project into a deployed service by following these tutorials

--------


#### labelbox_upload.ipynb
* Download images and prelabels
* Setup a labelbox project
* Upload prelabels to labelbox using MAL
* Clean up the data in labelbox

#### detectnet_v2_bounding_box.ipynb
* Plug in training data from previous step (or bring your own labelbox project)
* Train a model using TLT. Compare with a non-pretrained model
* Prune the model for more efficient deployment
* Convert the model to a TRT engine
* Deploy the model using Triton Inference Server 

