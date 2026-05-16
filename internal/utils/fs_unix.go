//go:build unix

package utils

import (
	"os"
	"syscall"
)

func openOutputFile(path string, force bool) (*os.File, error) {
	flags := syscall.O_WRONLY | syscall.O_CREAT | syscall.O_NOFOLLOW
	if force {
		flags |= syscall.O_TRUNC
	} else {
		flags |= syscall.O_EXCL
	}

	fd, err := syscall.Open(path, flags, 0644)
	if err != nil {
		return nil, err
	}

	return os.NewFile(uintptr(fd), path), nil
}
