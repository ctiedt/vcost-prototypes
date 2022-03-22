use std::{
    fs::File,
    sync::{Arc, Mutex},
    time::Duration,
};

use nokhwa::Camera;
use numpy::IntoPyArray;
use pyo3::{
    types::{IntoPyDict, PyFloat},
    Python,
};
use rand::random;
use rodio::{Decoder, OutputStream, Sink};

trait IntoDuration {
    fn millis(self) -> Duration;
    fn secs(self) -> Duration;
}

impl IntoDuration for u64 {
    fn millis(self) -> Duration {
        Duration::from_millis(self)
    }

    fn secs(self) -> Duration {
        Duration::from_secs(self)
    }
}

fn decide_music(emotion: &str, intensity: f64) -> File {
    let mut emotion = emotion;
    let n: u8 = random::<u8>() % 2u8 + 1;
    if intensity < 0.3 || !["happy", "angry", "sad", "neutral"].contains(&emotion) {
        emotion = "neutral";
    }
    File::open(format!("sounds/{}0{}.ogg", emotion, n)).unwrap()
}

fn py_thread(recv: Arc<Mutex<Option<ndarray::Array3<u8>>>>) -> anyhow::Result<()> {
    let (_stream, stream_handle) = OutputStream::try_default()?;
    let sink = Sink::try_new(&stream_handle)?;

    Python::with_gil(|py| -> anyhow::Result<()> {
        let fer = py.import("fer").unwrap();
        let locals = [("fer", fer)].into_py_dict(py);
        py.run(
            r#"
detector = fer.FER()
        "#,
            None,
            Some(locals),
        )
        .unwrap();

        loop {
            if let Some(frame) = recv.lock().unwrap().take() {
                locals.set_item("img", frame.into_pyarray(py))?;
                py.run(
                    r#"
(emotion, intensity) = detector.top_emotion(img)
"#,
                    None,
                    Some(locals),
                )
                .unwrap();
                if let (Some(emotion), Some(intensity)) =
                    (locals.get_item("emotion"), locals.get_item("intensity"))
                {
                    if emotion.is_none() || intensity.is_none() {
                        continue;
                    }
                    dbg!(emotion, intensity);
                    let emotion = emotion.str()?.to_str()?;
                    let intensity = intensity.downcast::<PyFloat>().unwrap().value();
                    let source = Decoder::new(decide_music(emotion, intensity))?;
                    sink.append(source);
                } else {
                    let source = Decoder::new(File::open("sounds/neutral01.ogg")?)?;

                    sink.append(source);
                }
                sink.play();
                sink.sleep_until_end();
            }
        }
    })?;

    Ok(())
}

fn main() -> anyhow::Result<()> {
    let cam_idx = std::env::args().nth(1).expect("Please call the program as `vcost_rs <id>` where id is the ID of your camera (probably 0, unless you have multiple cameras connected)");

    let shared_frame: Arc<Mutex<Option<ndarray::Array3<u8>>>> = Arc::new(Mutex::new(None));

    let cloned_frame = shared_frame.clone();
    let _py_thread_handle = std::thread::spawn(move || py_thread(cloned_frame));

    let mut camera = Camera::new(cam_idx.parse()?, None)?;
    camera.open_stream()?;
    loop {
        let frame = camera.frame()?;

        let w = frame.width() as usize;
        let h = frame.height() as usize;
        let v = frame.into_flat_samples().samples;
        let f = ndarray::Array3::from_shape_vec((h, w, 3), v)?;
        let mut data = shared_frame.lock().unwrap();
        data.replace(f);
    }
}
