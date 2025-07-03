'use client';
import React from 'react';

// chakra imports
import {
  Box,
  Button,
  Flex,
  Icon,
  Image,
  useColorModeValue,
} from '@chakra-ui/react';
import { IoArrowBack, IoLogOut } from 'react-icons/io5';
import logo from '/public/img/esb.png';

function Sidebar() {
  // Chakra Color Mode
  let sidebarBg = useColorModeValue('white', 'navy.800');
  let sidebarRadius = '14px';
  let sidebarMargins = '0px';
  // SIDEBAR
  return (
    <Flex
      direction="column"
      display={{ base: 'none', xl: 'flex' }}
      position="fixed"
      minH="100%"
      justifyContent="space-between"
    >
      <Box
        bg={sidebarBg}
        w="250px"
        my={{
          sm: '16px',
        }}
        h="calc(100vh - 32px)"
        m={sidebarMargins}
        borderRadius={sidebarRadius}
        minH="100%"
        p="20px"
        display="flex"
        flexDirection="column"
      >
        {/* Logo */}
        <Box mb="20px" textAlign="center">
          <Image src={logo.src} alt="Logo" boxSize="100px" mx="auto" />
        </Box>
        <Button
          leftIcon={<IoArrowBack />}
          variant="solid"
          colorScheme="red"
          bg="white"
          color="red.500"
          _hover={{ bg: 'red.100' }}
          _active={{ bg: 'red.200' }}
          mb="20px"
        >
          Retour
        </Button>
        <Flex flex="1" />
        {/* Log Out Button */}
        <Button
          leftIcon={<Icon as={IoLogOut} />}
          variant="solid"
          colorScheme="red"
          w="full"
          mt="auto"
          fontWeight="bold"
          justifyContent="flex-start"
        >
          Logout
        </Button>
      </Box>
    </Flex>
  );
}

export default Sidebar;
