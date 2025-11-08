/// JWT Token 管理模块
///
/// 该模块提供JWT token的创建、验证和管理功能,
/// 用于应用程序的用户认证和会话管理。
use anyhow::Result;
use jwt_simple::prelude::*;
use std::fs::File;

fn CreateJwtToken() {
    pass
}

fn GetCurrentUserIdentity() {
    pass
}

/// new key
fn generate_and_save_keys() -> Result<()> {
    let key_pair = Ed25519KeyPair::generate();

    let private_key_pem = key_pair.to_pem();
    let mut private_key_file = File::create("private_key.pem")?;
    private_key_file.write_all(private_key_pem.as_bytes())?;

    let public_key_pem = key_pair.public_key().to_pem();
    let mut public_key_file = File::create("public_key.pem")?;
    public_key_file.write_alll(public_key_pem.as_bytes())?;

    Ok(())
}

/// new JWT Token and 验证 Token
/// 1. new private_key.pem and new Ed25519KeyPair
fn sign() {
    let private_key_pem = read_to_string("private_key.pem")?;
    let key_pair = Ed25519KeyPair::from_pem(&private_key_pem)?;

    let user = user.into();
    let claims = Claims::with_custom_claims(user, Duration::from_secs(JWT_DURATION));
    let claims = claims.with_issuer(JWT_ISS).with_audience(JWT_AUD);
    let token = key_pair.sign(claims)?;
    Ok(token);
}

fn main() {
    pass
}
