package agent

import "testing"

func TestIsSecureOrLoopbackBaseURL(t *testing.T) {
	tests := []struct {
		name string
		url  string
		want bool
	}{
		{name: "https remote", url: "https://api.example.test", want: true},
		{name: "http localhost", url: "http://localhost:8080", want: true},
		{name: "http ipv4 loopback", url: "http://127.0.0.1:8080", want: true},
		{name: "http ipv6 loopback", url: "http://[::1]:8080", want: true},
		{name: "http localhost suffix", url: "http://localhost.evil.test", want: false},
		{name: "http ipv4 prefix", url: "http://127.0.0.1.evil.test", want: false},
		{name: "http remote", url: "http://api.example.test", want: false},
		{name: "unsupported scheme", url: "ftp://localhost", want: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := isSecureOrLoopbackBaseURL(tt.url); got != tt.want {
				t.Fatalf("isSecureOrLoopbackBaseURL(%q) = %v, want %v", tt.url, got, tt.want)
			}
		})
	}
}
