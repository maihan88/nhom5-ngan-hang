import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, ConfusionMatrixDisplay, RocCurveDisplay
from utils import *

def run(d):
    data=prediction_data(d)
    year=test_year(data)
    train,test=data[data.nam<year],data[data.nam==year]
    ytr,yte=train[TARGET],test[TARGET]
    sets={'Baseline':[], 'Financial Only':FIN, 'Financial + General Event':FIN+['co_su_kien'], 'Financial + Event Categories':FIN+CAT}
    performance=[]; coefficients=[]; predictions=[]; matrices=[]; scalers=[]
    fig,axes=plt.subplots(2,2,figsize=(10,9)); rocfig,rocax=plt.subplots(figsize=(7,6))
    for ax,(name,features) in zip(axes.flat,sets.items()):
        if name=='Baseline':
            model=DummyClassifier(strategy='most_frequent',random_state=42)
            xtr,xte=train[FIN],test[FIN]
        else:
            event=[c for c in features if c not in FIN]
            prep=ColumnTransformer([('financial',StandardScaler(),FIN),('events','passthrough',event)],verbose_feature_names_out=False)
            model=Pipeline([('preprocess',prep),('model',LogisticRegression(max_iter=1000,random_state=42))])
            xtr,xte=train[features],test[features]
        model.fit(xtr,ytr)
        pred=model.predict(xte); proba=model.predict_proba(xte)[:,1]
        tn,fp,fn,tp=confusion_matrix(yte,pred,labels=[0,1]).ravel()
        matrices.append({'Model':name,'TN':int(tn),'FP':int(fp),'FN':int(fn),'TP':int(tp)})
        performance.append({'Model':name,'Features':', '.join(features) or '-','Accuracy':accuracy_score(yte,pred),'Precision':precision_score(yte,pred,zero_division=0),'Recall':recall_score(yte,pred,zero_division=0),'F1':f1_score(yte,pred,zero_division=0),'ROC-AUC':roc_auc_score(yte,proba)})
        ConfusionMatrixDisplay.from_predictions(yte,pred,labels=[0,1],ax=ax,colorbar=False); ax.set_title(name)
        RocCurveDisplay.from_predictions(yte,proba,name=name,ax=rocax)
        for j,r in enumerate(test.itertuples()):
            predictions.append({'Model':name,'ma_nh':r.ma_nh,'quy':r.quy,'nam':r.nam,'actual':getattr(r,TARGET),'prediction':int(pred[j]),'probability_up':proba[j]})
        if name!='Baseline':
            for c,b in zip(features,model.named_steps['model'].coef_[0]):
                coefficients.append({'Model':name,'feature':c,'coefficient':b,'abs_coefficient':abs(b),'direction':'cùng chiều' if b>0 else 'ngược chiều','unit':'1 SD Train' if c in FIN else '1 đơn vị sự kiện'})
            # Kiểm chứng scaler thực sự chỉ fit 128 dòng Train.
            assert model.named_steps['preprocess'].named_transformers_['financial'].n_samples_seen_==len(train)
            fitted=model.named_steps['preprocess'].named_transformers_['financial']
            for c,mean,scale in zip(FIN,fitted.mean_,fitted.scale_):
                scalers.append({'Model':name,'feature':c,'train_mean':mean,'train_scale':scale,'samples_fit':len(train)})
    fig.tight_layout(); fig.savefig(FIGURES/'confusion_matrices.png',dpi=160); plt.close(fig)
    rocax.plot([0,1],[0,1],'k--'); rocfig.tight_layout(); rocfig.savefig(FIGURES/'roc_curves.png',dpi=160); plt.close(rocfig)
    co=pd.DataFrame(coefficients).sort_values(['Model','abs_coefficient'],ascending=[True,False])
    fig,axes=plt.subplots(1,3,figsize=(17,6))
    for ax,name in zip(axes, list(sets)[1:]):
        sub=co[co.Model.eq(name)].sort_values('coefficient'); ax.barh(sub.feature,sub.coefficient); ax.axvline(0,color='black'); ax.set_title(name)
    fig.tight_layout(); fig.savefig(FIGURES/'logistic_coefficients.png',dpi=160); plt.close(fig)
    result=pd.DataFrame(performance)
    save(result,'model_comparison'); save(co,'logistic_coefficients'); save(pd.DataFrame(predictions),'test_predictions')
    save(pd.DataFrame(matrices),'confusion_matrices'); save(pd.DataFrame(scalers),'logistic_scaler_parameters')
    counts=pd.crosstab(data[data.nam<=year].nam.map(lambda x:'Train' if x<year else 'Test'),data[TARGET])
    counts.plot.bar(); plt.ylabel('Observations'); plt.tight_layout(); plt.savefig(FIGURES/'target_distribution.png',dpi=160); plt.close()
    return result,co
