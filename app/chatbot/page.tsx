'use client';
import { Box, Input, Button, VStack, Text, Flex, Icon, Image, InputGroup, InputLeftElement, Menu, MenuButton, MenuList, MenuItem, HStack, useToast } from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { IoArrowBack, IoLogOut, IoSend, IoSearch, IoPersonCircle, IoEye, IoCopy, IoRefresh } from 'react-icons/io5';
import axios from 'axios';
import logo from '/public/img/esb.png';

export default function ChatbotPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<{ text: string; sender: 'bot' | 'user' }[]>([]);
  const [input, setInput] = useState('');
  const [agentActive, setAgentActive] = useState(false);
  const toast = useToast();

  useEffect(() => {
    // Add default message when the component mounts
    setMessages([{ text: "Bonjour, comment peux-je vous aider aujourd'hui?", sender: 'bot' }]);
  }, []);

  const handleExampleClick = async (example: string) => {
    setInput(example);
    setTimeout(() => {
      handleSend(example);
    }, 0);
  };

  const handleSend = async (overrideInput?: string) => {
    const messageToSend = overrideInput !== undefined ? overrideInput : input;
    if (messageToSend.trim()) {
      setMessages(prev => [...prev, { text: messageToSend, sender: 'user' }]);
      setAgentActive(true);
      setInput('');
      // Show toast notification
      const toastId = toast({
        title: 'Generating response...',
        status: 'info',
        duration: 2000,
        isClosable: true,
      });
      try {
        const res = await axios.post('http://localhost:5000/api/chat', { message: messageToSend });
        setMessages(prev => [...prev, { text: res.data.response, sender: 'bot' }]);
      } catch (err) {
        setMessages(prev => [
          ...prev,
          { text: 'Error: Unable to connect to backend.', sender: 'bot' }
        ]);
      }
      setAgentActive(false);
      // Optionally close the toast if still open
      toast.closeAll();
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Message copied to clipboard!');
  };

  const handleRefresh = () => {
    alert('Refreshing the answer...');
  };

  const handleLogout = () => {
    localStorage.removeItem('authenticated'); // Remove authentication
    router.push('/login'); // Redirect to login page
  };

  return (
    <Flex w="100vw" h="100vh">
      {/* Sidebar */}
      <Flex
        direction="column"
        w="250px"
        bg="red.500"
        color="white"
        p="20px"
        justifyContent="space-between"
      >
        <Box>
          <Image src={logo.src} alt="Logo" boxSize="120px" mx="auto" mb="20px" />
          <Button
            leftIcon={<IoArrowBack />}
            variant="solid"
            bg="white"
            color="red.500"
            _hover={{ bg: 'red.100' }}
            _active={{ bg: 'red.200' }}
            w="full"
            mb="20px"
            onClick={() => router.push('/welcome')}
          >
            Back
          </Button>
        </Box>
        <Button
          leftIcon={<IoLogOut />}
          variant="solid"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          w="full"
          onClick={handleLogout}
        >
          Log Out
        </Button>
      </Flex>

      {/* Chatbot Container */}
      <Flex
        flex="1"
        direction="column"
        bg="gray.100"
        p="20px"
      >
        {/* Search Bar and Profile */}
        <Flex justifyContent="space-between" alignItems="center" mb="10px">
          <InputGroup w="300px">
            <InputLeftElement pointerEvents="none">
              <Icon as={IoSearch} color="gray.400" />
            </InputLeftElement>
            <Input
              placeholder="Search..."
              bg="white"
              borderRadius="md"
              _placeholder={{ color: 'gray.400' }}
            />
          </InputGroup>
          <Menu>
            <MenuButton>
              <Icon as={IoPersonCircle} w="40px" h="40px" color="gray.600" cursor="pointer" />
            </MenuButton>
            <MenuList>
              <MenuItem>
                <Text fontWeight="bold">Zayneb Zouaoui</Text>
              </MenuItem>
            </MenuList>
          </Menu>
        </Flex>

        <Flex
          flex="1"
          direction="row"
          bg="gray.100"
          p="20px"
        >
          {/* Chatbot Content */}
          <Flex
            flex="1"
            direction="column"
            alignItems="center"
            justifyContent="center"
          >
            <Box
              w="80%"
              h="80%"
              bg="white"
              borderRadius="md"
              boxShadow="md"
              p="20px"
              textAlign="center"
            >
              <Text fontSize="2xl" fontWeight="bold" mb="20px" color="red.500">
                Student Chatbot
              </Text>
              <VStack spacing="10px" align="start" h="calc(100% - 60px)">
                <Box
                  w="100%"
                  flex="1"
                  bg="gray.50"
                  borderRadius="md"
                  overflowY="auto"
                  p="10px"
                  boxShadow="inner"
                >
                  {messages.map((msg, idx) => (
                    <Flex
                      key={idx}
                      justifyContent={msg.sender === 'bot' ? 'flex-start' : 'flex-end'}
                      mb="5px"
                    >
                      <Box
                        bg={msg.sender === 'bot' ? 'red.100' : 'blue.100'}
                        p="10px"
                        borderRadius="md"
                        maxW="70%"
                      >
                        <Text>{msg.text}</Text>
                      </Box>
                      {msg.sender === 'bot' && (
                        <HStack spacing="5px" ml="10px">
                          <Icon
                            as={IoCopy}
                            w="16px"
                            h="16px"
                            color="gray.500"
                            cursor="pointer"
                            onClick={() => handleCopy(msg.text)}
                          />
                          <Icon
                            as={IoRefresh}
                            w="16px"
                            h="16px"
                            color="gray.500"
                            cursor="pointer"
                            onClick={handleRefresh}
                          />
                        </HStack>
                      )}
                    </Flex>
                  ))}
                </Box>
                <Flex w="100%" alignItems="center">
                  <Input
                    placeholder="Type your message..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSend();
                    }}
                    flex="1"
                    borderRadius="md"
                    bg="gray.50"
                  />
                  <Button
                    ml="10px"
                    colorScheme="red"
                    onClick={() => handleSend()}
                    p="0"
                    w="40px"
                    h="40px"
                    borderRadius="full"
                    isLoading={agentActive}
                    loadingText="Sending"
                  >
                    <Icon as={IoSend} w="20px" h="20px" />
                  </Button>
                </Flex>
              </VStack>
            </Box>
          </Flex>

          {/* Right Sidebar */}
          <Box
            w="300px"
            bg="white"
            borderRadius="md"
            boxShadow="md"
            p="20px"
            ml="20px"
          >
            <Text fontSize="lg" fontWeight="bold" mb="10px" color="gray.700">
              Agent Status
            </Text>
            <VStack spacing="5px" align="start" mb="20px">
              <Text> SentimentAgent </Text>
              <Text> IntentAgent </Text>
              <Text> WebAgent </Text>
              <Text> RefinerAgent </Text>
              <Text> SelfReflectionAgent </Text>
            </VStack>
            <Text fontSize="lg" fontWeight="bold" mb="10px" color="gray.700">
              Try These Examples
            </Text>
            <VStack spacing="5px" align="start">
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("I love the entrepreneurship program at ESB!")}
              > "I love the entrepreneurship program at ESB!"</Text>
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("I'm frustrated with the registration system!")}
              >"I'm frustrated with the registration system!"</Text>
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("What are the library hours?")}
              > "What are the library hours?"</Text>
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("I need career guidance for my future")}
              > "I need career guidance for my future"</Text>
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("Thank you for the excellent support!")}
              > "Thank you for the excellent support!"</Text>
              <Text
                as="span"
                cursor="pointer"
                _hover={{ textDecoration: 'underline', color: 'red.500' }}
                onClick={() => handleExampleClick("J'adore ESB!")}
              > "J'adore ESB! "</Text>
            </VStack>
          </Box>
        </Flex>
      </Flex>
    </Flex>
  );
}
