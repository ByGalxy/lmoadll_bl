use chrono::Local;
use env_logger::Env;
use log::Level;
use std::io::Write;


pub(crate) fn init_logger() {
    let env = Env::default().filter_or("MY_LOG_LEVEL", "debug");

    env_logger::Builder::from_env(env)
        .format(|buf, record| {
            let (level_str, level_style) = match record.level() {
                Level::Error => ("ERR", anstyle::Style::new().fg_color(Some(anstyle::AnsiColor::Red.into())).bold()),
                Level::Warn => ("WRN", anstyle::Style::new().fg_color(Some(anstyle::AnsiColor::Yellow.into())).bold()),
                Level::Info => ("INF", anstyle::Style::new().fg_color(Some(anstyle::AnsiColor::Green.into())).bold()),
                Level::Debug => ("DBG", anstyle::Style::new().fg_color(Some(anstyle::AnsiColor::Cyan.into())).bold()),
                Level::Trace => ("TRC", anstyle::Style::new().fg_color(Some(anstyle::AnsiColor::Cyan.into())).bold()),
            };

            writeln!(
                buf,
                "{} {}{} [{}] {}{}",
                Local::now().format("%H:%M:%S"),
                level_style,
                level_str,
                record.module_path().unwrap_or("<unnamed>"),
                anstyle::Reset,
                record.args()
            )
        })
        .filter(None, log::LevelFilter::Debug)
        .init();
}