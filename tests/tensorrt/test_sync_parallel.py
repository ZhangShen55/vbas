import asyncio
import importlib.util
from pathlib import Path
import sys
import threading
from types import SimpleNamespace, ModuleType
import unittest
from unittest.mock import patch
import numpy as np


def load_service():
    settings = SimpleNamespace(Person_Thresd={k: .25 for k in ('Head','Top_Head','Hat','Headphones','Shoulder')}, Face_Thresd={'face': .1}, IMAGE_ROOT='/tmp', SAVE_RESULT_IMAGE=False)
    fake = ModuleType('core.settings')
    for k,v in dict(settings=settings,yolo_person_model=None,yolo_face_model=None,use_half=True,Total_HaveProcess_Tasks={'val':0}).items():setattr(fake,k,v)
    spec=importlib.util.spec_from_file_location('sync_parallel_test_service',Path(__file__).resolve().parents[2]/'services/task_service_base64.py');m=importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules,{'core.settings':fake,'cv2':ModuleType('cv2')}):spec.loader.exec_module(m)
    return m


class ParallelTests(unittest.IsolatedAsyncioTestCase):
    async def test_barrier_proves_overlap_and_preserves_results(self):
        m=load_service();barrier=threading.Barrier(2);calls=[]
        class Model:
            def __init__(self,data):self.data=data
            def predict(self,img,**kw):
                calls.append(kw);barrier.wait(timeout=3)
                return [SimpleNamespace(boxes=SimpleNamespace(data=SimpleNamespace(tolist=lambda:self.data)))]
        m.yolo_person_model=Model([[1,2,3,4,.9,0],[1,2,3,4,.2,1],[1,2,3,4,.9,5]])
        m.yolo_face_model=Model([[2,3,4,5,.8,0],[1,2,3,4,.05,0]])
        p,f=await m._detect_models_parallel(np.zeros((2,2,3)),(10,20),1088,1920,0)
        self.assertEqual(p.PersonCnt,1);self.assertEqual(f.FaceCnt,1)
        self.assertEqual(p.Personlist[0].ROI.LeftTopX,11);self.assertEqual(f.Facelist[0].ROI.LeftTopY,23)
        self.assertTrue(next(x for x in calls if 'agnostic_nms' in x)['agnostic_nms'])
        self.assertTrue(all(x['half'] and x['conf']==.1 and x['imgsz']==(1088,1920) for x in calls))

    async def test_failure_and_cancellation_drain_other_branch(self):
        for cancel in (False,True):
            m=load_service();started=threading.Event();release=threading.Event();finished=threading.Event()
            def person(*a):
                started.wait(3)
                if not cancel:raise ValueError('person failed')
                return 'person'
            def face(*a):
                started.set();release.wait(3);finished.set();return 'face'
            m._detect_person=person;m._detect_face=face
            task=asyncio.create_task(m._detect_models_parallel(None,None,1,1,0))
            await asyncio.to_thread(started.wait,3)
            if cancel:task.cancel()
            await asyncio.sleep(.02);self.assertFalse(task.done());release.set()
            with self.assertRaises(asyncio.CancelledError if cancel else ValueError):await task
            self.assertTrue(finished.is_set())

    async def test_empty_roi_skips_models(self):
        m=load_service();m.mask_polygon=lambda *a:(np.zeros((0,0,3)),(0,0))
        result=await m.process_polygon(0,SimpleNamespace(Label='empty',Points=[]),None,1088,1920,'t')
        self.assertEqual(result.PersonInfo.PersonCnt,0);self.assertEqual(result.FaceInfo.FaceCnt,0)

    async def test_multiple_rois_remain_sequential_and_ordered(self):
        m=load_service();m.cv2.imdecode=lambda *a:np.zeros((2,2,3));m.cv2.IMREAD_COLOR=1;events=[]
        async def polygon(idx,poly,*a):
            events.append(('start',idx));await asyncio.sleep(0);events.append(('end',idx))
            return m.PolygonResult(Label=poly.Label,PersonInfo=m.PersonInfo(PersonCnt=0,Personlist=[]),FaceInfo=m.FaceInfo(FaceCnt=0,Facelist=[]))
        m.process_polygon=polygon
        request=SimpleNamespace(TaskID='t',ImageList=[SimpleNamespace(Data='aGk=',ImageID='i')],AnalysisRule=SimpleNamespace(AlgParams=SimpleNamespace(ImageResolution=SimpleNamespace(ImageWidth=1920,ImageHeight=1088),PolygonList=[SimpleNamespace(Label='a',Points=[]),SimpleNamespace(Label='b',Points=[])],ResultImageDeclare=0)))
        response=await m.sync_tasks_data(request)
        self.assertEqual(events,[('start',0),('end',0),('start',1),('end',1)])
        self.assertEqual([x.Label for x in response.TaskResult[0].KedaPersonObject.PolygonResult],['a','b'])
