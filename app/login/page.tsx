'use client';
import { Box, Button, Input, VStack, Text, Flex, Checkbox, Image, InputGroup, InputRightElement, IconButton } from '@chakra-ui/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';
import { IoEye, IoEyeOff } from 'react-icons/io5';
import logo from '/public/img/esb.png';

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectPath = searchParams.get('redirect') || '/welcome';
  const [isFlipped, setIsFlipped] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [registerUsername, setRegisterUsername] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loginSuccess, setLoginSuccess] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      alert('Please enter valid credentials.');
      return;
    }
    try {
      const res = await fetch('http://localhost:5000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        setLoginSuccess(true);
        router.push(redirectPath);
      } else {
        alert(data.error || 'Login failed.');
      }
    } catch (err) {
      alert('Network error.');
    }
  };

  useEffect(() => {
    if (loginSuccess) {
      localStorage.setItem('authenticated', 'true');
    }
  }, [loginSuccess]);

  const handleRegister = async () => {
    if (!registerUsername || !registerPassword || !confirmPassword) {
      alert('Please fill in all fields.');
      return;
    }
    if (registerPassword !== confirmPassword) {
      alert('Passwords do not match.');
      return;
    }
    try {
      const res = await fetch('http://localhost:5000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: registerUsername, password: registerPassword, confirm_password: confirmPassword }),
        credentials: 'include',
      });
      const data = await res.json();
      if (res.ok) {
        alert('Registration successful! Please log in.');
        setIsFlipped(false);
      } else {
        alert(data.error || 'Registration failed.');
      }
    } catch (err) {
      alert('Network error.');
    }
  };

  return (
    <Flex
      w="100vw"
      h="100vh"
      alignItems="center"
      justifyContent="center"
      bg="gray.100"
    >
      <Box
        w="400px"
        h="400px"
        bg="white"
        borderRadius="md"
        boxShadow="md"
        p="20px"
        textAlign="center"
        style={{ perspective: '1000px' }}
      >
        <Box
          w="100%"
          h="100%"
          position="relative"
          transition="transform 0.6s"
          transform={isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)'}
          style={{ transformStyle: 'preserve-3d' }}
        >
          {/* Login Form */}
          <Box
            position="absolute"
            w="100%"
            h="100%"
            style={{ backfaceVisibility: 'hidden' }}
          >
            <Image src={logo.src} alt="Logo" boxSize="80px" mx="auto" mb="10px" />
            <Text fontSize="2xl" fontWeight="bold" mb="10px" color="red.500">
              Login
            </Text>
            <VStack spacing="10px">
              <Input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
              <InputGroup>
                <Input
                  placeholder="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <InputRightElement>
                  <IconButton
                    aria-label="Toggle Password Visibility"
                    icon={showPassword ? <IoEye /> : <IoEyeOff />}
                    size="sm"
                    onClick={() => setShowPassword(!showPassword)}
                  />
                </InputRightElement>
              </InputGroup>
              <Checkbox alignSelf="start">
                Remember Me
              </Checkbox>
              <Button colorScheme="red" w="100%" onClick={handleLogin}>
                Login
              </Button>
              <Button
                variant="link"
                color="blue.500"
                onClick={() => setIsFlipped(true)}
              >
                You don't have an account? Sign up
              </Button>
            </VStack>
          </Box>

          {/* Register Form */}
          <Box
            position="absolute"
            w="100%"
            h="100%"
            style={{ backfaceVisibility: 'hidden' }}
            transform="rotateY(180deg)"
          >
            <Image src={logo.src} alt="Logo" boxSize="80px" mx="auto" mb="10px" />
            <Text fontSize="2xl" fontWeight="bold" mb="10px" color="red.500">
              Register
            </Text>
            <VStack spacing="10px">
              <Input
                placeholder="Username"
                value={registerUsername}
                onChange={(e) => setRegisterUsername(e.target.value)}
                autoComplete="username"
              />
              <InputGroup>
                <Input
                  placeholder="Password"
                  type={showRegisterPassword ? 'text' : 'password'}
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                />
                <InputRightElement>
                  <IconButton
                    aria-label="Toggle Password Visibility"
                    icon={showRegisterPassword ? <IoEye /> : <IoEyeOff />}
                    size="sm"
                    onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                  />
                </InputRightElement>
              </InputGroup>
              <InputGroup>
                <Input
                  placeholder="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
                <InputRightElement>
                  <IconButton
                    aria-label="Toggle Confirm Password Visibility"
                    icon={showConfirmPassword ? <IoEye /> : <IoEyeOff />}
                    size="sm"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  />
                </InputRightElement>
              </InputGroup>
              <Button colorScheme="red" w="100%" onClick={handleRegister}>
                Register
              </Button>
              <Button
                variant="link"
                color="blue.500"
                onClick={() => setIsFlipped(false)}
              >
                Already have an account? Login
              </Button>
            </VStack>
          </Box>
        </Box>
      </Box>
    </Flex>
  );
}
