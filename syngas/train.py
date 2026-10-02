"""Entrena la arquitectura del notebook y exporta inferencia portable al navegador."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('MPLCONFIGDIR', '/tmp/syngas-mpl')
os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
ROOT = Path(__file__).resolve().parent
INPUTS = ['C','H','O','Moisture','Ash','FC','VM','ER','T','SB']
OUTPUTS = ['H2','CO','CO2','CH4','LHV']
file = ROOT/'data/base_datos_ANN.xlsx'
df = pd.read_excel(file, sheet_name='Hoja1'); df.columns = df.columns.str.strip()
ext = pd.read_excel(file, sheet_name='Hoja2'); ext.columns = ext.columns.str.strip()
for frame in [df,ext]:
    assert np.isfinite(frame[INPUTS+OUTPUTS].to_numpy()).all()
Xtr, Xtmp, ytr, ytmp = train_test_split(df[INPUTS],df[OUTPUTS],test_size=.4,random_state=42)
Xval,Xtest,yval,ytest = train_test_split(Xtmp,ytmp,test_size=.5,random_state=42)
sx,sy = MinMaxScaler(),MinMaxScaler()
x,y=sx.fit_transform(Xtr),sy.fit_transform(ytr)
tf.keras.utils.set_random_seed(42)
model=tf.keras.Sequential([tf.keras.layers.Input(shape=(10,)),tf.keras.layers.Dense(10,activation='tanh'),tf.keras.layers.Dense(5)])
model.compile(optimizer='adam',loss='mse',metrics=['mae'])
# Explicit small thread pools suit the cloud machine; architecture and split match notebook.
options=tf.data.Options(); options.threading.private_threadpool_size=1
train=tf.data.Dataset.from_tensor_slices((x,y)).shuffle(len(x),seed=42).batch(16).with_options(options)
val=tf.data.Dataset.from_tensor_slices((sx.transform(Xval),sy.transform(yval))).batch(16).with_options(options)
history=model.fit(train,validation_data=val,epochs=400,callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=30,restore_best_weights=True)],verbose=0,shuffle=False)
def predict(frame):
    return sy.inverse_transform(model(sx.transform(frame).astype('float32'),training=False).numpy())
def metrics(real,pred):
    return {name:{'mae':float(mean_absolute_error(real[:,i],pred[:,i])),'rmse':float(np.sqrt(mean_squared_error(real[:,i],pred[:,i]))),'r':float(np.corrcoef(real[:,i],pred[:,i])[0,1])} for i,name in enumerate(OUTPUTS)}
weights=[w.tolist() for w in model.get_weights()]
metadata={'inputs':INPUTS,'outputs':OUTPUTS,'weights':weights,'xMin':sx.data_min_.tolist(),'xMax':sx.data_max_.tolist(),'yMin':sy.data_min_.tolist(),'yMax':sy.data_max_.tolist(),'examples':df[INPUTS].head(3).to_dict(orient='records'),'epochs':len(history.history['loss']),'counts':{'train':len(Xtr),'validation':len(Xval),'test':len(Xtest),'external':len(ext)},'metrics':{'test':metrics(ytest.to_numpy(),predict(Xtest)),'external':metrics(ext[OUTPUTS].to_numpy(),predict(ext[INPUTS]))},'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'history':history.history,'unitsConfirmed':True}
(ROOT/'web/model.js').write_text('window.SYNGAS_MODEL = '+json.dumps(metadata,allow_nan=False)+';\n')
(ROOT/'model.keras').parent.mkdir(exist_ok=True)
model.save(ROOT/'model.keras')
reference={'inputs':ext[INPUTS].to_numpy().tolist(),'predictions':predict(ext[INPUTS]).tolist()}
(ROOT/'reference_predictions.json').write_text(json.dumps(reference))
print(json.dumps({'epochs':metadata['epochs'],'counts':metadata['counts'],'metrics':metadata['metrics']},indent=2))
