## sample creation 

### Generate random sample
sample within subpolygon   | or across full AOI
:-------------------------:|:-------------------------:
![](images/sample_pts1.png)  |  ![](images/sample_pts2.png) 

### Shift sample points to centroids of reference grid
![](images/shift_sample_pts.png)

### Populate neighbor pixels for contextual information
![](images/sample_neighborhood.png)


## setup for database creation / editing
conda create --name venv.collect_sql python=3.8
conda activate venv.collect_sql
conda install sqlalchemy pyqt5