package com.pala.app.data.remote.dto

data class ApiEnvelope<T>(
    val success: Boolean,
    val data: T?,
    val error: String?,
)

data class LoginRequest(
    val email: String,
    val password: String,
)

data class RegisterRequest(
    val email: String,
    val password: String,
)

data class UserDto(
    val id: String,
    val email: String,
    val is_active: Boolean,
)

data class TokenDto(
    val access_token: String,
    val refresh_token: String,
    val token_type: String,
)

data class AuthData(
    val user: UserDto,
    val tokens: TokenDto,
)

data class RefreshRequest(
    val refresh_token: String,
)

data class RefreshData(
    val tokens: TokenDto,
)
