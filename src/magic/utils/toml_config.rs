use pyo3::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::path::Path;


const CONFIG_PATH: &str = "config.toml";


/// 检查配置文件是否存在并读取指定字段的值
#[pyfunction]
pub fn coexistent_config_toml(section: &str, key: &str) -> PyResult<Option<String>> {
    if !Path::new(CONFIG_PATH).exists() {
        return Ok(None);
    }
    
    match fs::read_to_string(CONFIG_PATH) {
        Ok(content) => {
            match toml::from_str::<HashMap<String, HashMap<String, String>>>(&content) {
                Ok(config) => {
                    if let Some(section_map) = config.get(section) {
                        if let Some(value) = section_map.get(key) {
                            return Ok(Some(value.clone()));
                        }
                    }
                    Ok(None)
                },
                Err(_) => Ok(None)
            }
        },
        Err(_) => Ok(None)
    }
}


/// 检查键并写入配置文件
#[pyfunction]
pub fn write_config_toml(section: &str, key: &str, value: &str) -> PyResult<()> {
    let mut config: HashMap<String, HashMap<String, String>> = HashMap::new();
    
    // 如果配置文件存在，尝试读取现有配置
    if Path::new(CONFIG_PATH).exists() {
        if let Ok(content) = fs::read_to_string(CONFIG_PATH) {
            if let Ok(existing_config) = toml::from_str::<HashMap<String, HashMap<String, String>>>(&content) {
                config = existing_config;
            }
        }
    }
    
    // 确保section存在
    config.entry(section.to_string()).or_insert_with(HashMap::new)
        .insert(key.to_string(), value.to_string());
    
    // 写回配置文件
    match toml::to_string(&config) {
        Ok(toml_content) => {
            fs::write(CONFIG_PATH, toml_content)?;
            Ok(())
        },
        Err(e) => Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }
}


/// Python模块定义 - 使用pyo3 0.27.1兼容的签名
#[pymodule]
fn toml_config(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(coexistent_config_toml, m)?)?;
    m.add_function(wrap_pyfunction!(write_config_toml, m)?)?;
    Ok(())
}
